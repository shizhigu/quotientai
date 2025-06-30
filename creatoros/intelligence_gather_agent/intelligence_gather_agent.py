from google.adk.agents import SequentialAgent, LlmAgent, ParallelAgent
from creatoros.intelligence_gather_agent.brand_intelligence_agent import brand_intelligence_agent

class IntelligenceGatherAgent(SequentialAgent):
    def __init__(self):
        super().__init__(
            name="IntelligenceGatherAgent",
            # description="You are an intelligence gather agent. You are responsible for gathering intelligence about collaboration between a creator and a brand.",
            sub_agents=[brand_intelligence_agent],
        )

intelligence_gather_agent = brand_intelligence_agent # IntelligenceGatherAgent()