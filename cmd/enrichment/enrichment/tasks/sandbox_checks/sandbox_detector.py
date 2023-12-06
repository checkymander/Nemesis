# Standard Libraries
import asyncio
from typing import List

# 3rd Party Libraries
import nemesiscommon.constants as constants
import nemesispb.nemesis_pb2 as pb
import structlog
from enrichment.tasks.sandbox_checks.categorizer import \
    SandboxDetectorInterface
from nemesiscommon.messaging import (MessageQueueConsumerInterface,
                                     MessageQueueProducerInterface)
from nemesiscommon.tasking import TaskInterface
from prometheus_async import aio
from prometheus_client import Summary

logger = structlog.get_logger(module=__name__)


class SandboxDetector(TaskInterface):
    categorizer: SandboxDetectorInterface
    out_q_detector: MessageQueueProducerInterface

    def __init__(
        self,
        in_q_agent_data: MessageQueueConsumerInterface,
        out_q_agent_data: MessageQueueProducerInterface,
        categorizer: SandboxDetectorInterface
    ):
        self.in_q_agent_data = in_q_agent_data
        self.out_q_agent_data = out_q_agent_data
        self.categorizer = categorizer

    async def run(self) -> None:
        await self.in_q_agent_data.Read(self.agent_data_message)
        await asyncio.Future()

    @aio.time(Summary("sandbox_process_data_enriched", "Time spent checking sandbox"))  # type: ignore
    async def process_message(self, ingestedAgentDataMsg: pb.AgentDataIngestionMessage) -> None:
        total_hosts = len(ingestedAgentDataMsg.data)
        await logger.adebug("Received AgentDataIngestionMessage, checking if in a sandbox", total_procs=total_hosts)

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
    async def process_message(self, ingestedAgentDataMsg: pb.AgentDataIngestionMessage) -> None:
        total_hosts = len(ingestedAgentDataMsg.data)

        await logger.adebug("Received AgentDataIngestionMessage, checking sandbox", total_procs=total_hosts)

        enrichedDataIngestionMessage = pb.AgentDataEnrichedMessage()
        enrichedDataIngestionMessage.metadata.CopyFrom(ingestedAgentDataMsg.metadata)

        for i in range(total_hosts):
            ingestedAgent = ingestedAgentDataMsg.data[i]
            enrichedAgent = pb.AgentDataEnriched()
            enrichedProc = pb.ProcessEnriched()
            enrichedAgent.origin.CopyFrom(ingestedAgent)

            enrichments_success: List[str] = []
            # enrichments_failure = []


            # Check if the agent is in sandbox
            sandbox = await self.categorizer.check_sandbox(ingestedAgent.username, ingestedAgent.hostname)

            # right now there is no failure mode for the lookup so there are no enrichments_failure
            enrichments_success.append(constants.E_AGENT_DATA)

            enrichedAgent.sandbox = sandbox

            enrichedAgent.enrichments_success.extend(enrichments_success)

            enrichedDataIngestionMessage.data.append(enrichedProc)

        await self.out_q_process.Send(enrichedDataIngestionMessage.SerializeToString())
