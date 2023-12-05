# Standard Libraries
import asyncio
from typing import List

# 3rd Party Libraries
import nemesiscommon.constants as constants
import nemesispb.nemesis_pb2 as pb
import structlog
from enrichment.tasks.sandbox_checks.categorizer import SandboxDetectorInterface
from nemesiscommon.messaging import (
    MessageQueueConsumerInterface,
    MessageQueueProducerInterface,
)
from nemesiscommon.tasking import TaskInterface
from prometheus_async import aio
from prometheus_client import Summary

logger = structlog.get_logger(module=__name__)

class SandboxDetector(TaskInterface):
    categorizer: SandboxDetectorInterface
    out_q_detector: MessageQueueProducerInterface

    def __init__(
        self,
        in_q_username: MessageQueueConsumerInterface,
        in_q_hostname: MessageQueueConsumerInterface,
        out_q_sandbox: MessageQueueProducerInterface,
        categorizer: SandboxDetectorInterface
    ):
        self.in_q_username = in_q_username
        self.in_q_hostname = in_q_hostname
        self.out_q_sandbox = out_q_sandbox
        self.categorizer  = categorizer



class ProcessCategorizer(TaskInterface):
    categorizer: SandboxDetectorInterface
    out_q_process: MessageQueueProducerInterface

    def __init__(
        self,
        in_q_process: MessageQueueConsumerInterface,
        out_q_processenriched: MessageQueueProducerInterface,
        categorizer: SandboxDetectorInterface,
    ):
        self.in_q_process = in_q_process
        self.out_q_process = out_q_processenriched
        self.categorizer = categorizer

    async def run(self) -> None:
        await self.in_q_process.Read(self.process_message)  # type: ignore
        await asyncio.Future()

    @aio.time(Summary("sandbox_process_data_enriched", "Time spent checking sandbox"))  # type: ignore
    async def process_message(self, ingestedProcMsg: pb.ProcessIngestionMessage) -> None:
        total_procs = len(ingestedProcMsg.data)

        await logger.adebug("Received ProcessIngestionMessage", total_procs=total_procs)

        enrichedProcMsg = pb.ProcessEnrichedMessage()
        enrichedProcMsg.metadata.CopyFrom(ingestedProcMsg.metadata)

        for i in range(total_procs):
            ingestedProc = ingestedProcMsg.data[i]

            enrichedProc = pb.ProcessEnriched()
            enrichedProc.origin.CopyFrom(ingestedProc)

            enrichments_success: List[str] = []
            # enrichments_failure = []

            category = await self.categorizer.lookup(ingestedProc.name)

            # right now there is no failure mode for the lookup so there are no enrichments_failure
            enrichments_success.append(constants.E_PROCESS_CATEGORY)

            enrichedProc.category.category = category.category
            if category.description:
                enrichedProc.category.description = category.description

            enrichedProc.enrichments_success.extend(enrichments_success)
            enrichedProcMsg.data.append(enrichedProc)

        await self.out_q_process.Send(enrichedProcMsg.SerializeToString())
