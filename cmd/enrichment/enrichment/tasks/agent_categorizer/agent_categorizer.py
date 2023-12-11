# Standard Libraries
import asyncio
from typing import List

# 3rd Party Libraries
import nemesiscommon.constants as constants
import nemesispb.nemesis_pb2 as pb
import structlog
from nemesiscommon.messaging import (MessageQueueConsumerInterface, MessageQueueProducerInterface)
from nemesiscommon.tasking import TaskInterface
from prometheus_async import aio
from prometheus_client import Summary

logger = structlog.get_logger(module=__name__)

class AgentCategorizer(TaskInterface):
    in_q_agent_data: MessageQueueConsumerInterface
    out_q_agent_data: MessageQueueProducerInterface

    def __init__(
        self,
        in_q_agent_data: MessageQueueConsumerInterface,
        out_q_agent_data: MessageQueueProducerInterface,
    ):
        self.in_q_agent_data = in_q_agent_data
        self.out_q_agent_data = out_q_agent_data

    async def run(self) -> None:
        # Get Message from the input queue
        await self.in_q_agent_data.Read(self.process_message)  # type: ignore
        await asyncio.Future()

    @aio.time(Summary("agent_data_process_enriched", "Time spent checking sandbox"))  # type: ignore
    async def process_message(self, ingestedAgentDataMsg: pb.AgentDataIngestionMessage) -> None:
        total_hosts = len(ingestedAgentDataMsg.data)

        await logger.adebug("Received AgentDataIngestionMessage, creating sandbox message", total_procs=total_hosts)

        # Create our sandbox output message container
        out_sandboxAgentCheckMessage = pb.SandboxHostCheckIngestionMessage()
        out_sandboxAgentCheckMessage.metadata.CopyFrom(ingestedAgentDataMsg.metadata)
        out_sandboxAgentCheckMessage.data = pb.SandboxHostCheckIngestion()

        # This task just analyzes all input agent data and sends it to the right locations based on the tasks available to it
        for ingestedAgent in ingestedAgentDataMsg.data:
            # We have new agents to process, let's start with sandbox checks
            # Create
            sandboxAgentCheck = pb.SandboxHostCheckIngestion()
            sandboxAgentCheck.username = ingestedAgent.username
            sandboxAgentCheck.hostname = ingestedAgent.hostname
            sandboxAgentCheck.id = ingestedAgent.id

            out_sandboxAgentCheckMessage.data.append(sandboxAgentCheck)

        await logger.adebug("Passing off sandbox message to next queue", total_procs=total_hosts)
        await self.out_q_agent_data.Send(out_sandboxAgentCheckMessage.SerializeToString())
