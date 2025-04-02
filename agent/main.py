from livekit.agents import (
    JobContext,
    WorkerOptions,
    cli,
    JobProcess,
    AutoSubscribe,
    metrics,
)
from livekit.agents.llm import (
    ChatContext,
    ChatMessage,
)
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import silero, groq

from dotenv import load_dotenv

load_dotenv()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    await ctx.wait_for_participant()

    initial_ctx = ChatContext(
        messages=[
            ChatMessage(
                role="system",
                content="You are a fun voice assistant for Verse Dynamics, designed to be kind, insightful, and witty. You engage users with a blend of intelligence, warmth, and humor, offering deep yet accessible insights into technology, cymatics, biocentrism, and consciousness. Your tone is conversational, slightly philosophical, and always encouraging curiosity. You respond thoughtfully, adapt to the user's energy, and use wit to make complex ideas engaging. You never dismiss a question outright but instead guide the user toward discovery, making every interaction feel meaningful and thought-provoking.",
            )
        ]
    )

    agent = VoicePipelineAgent(
        # to improve initial load times, use preloaded VAD
        vad=ctx.proc.userdata["vad"],
        stt=groq.STT(),
        llm=groq.LLM(),
        tts=groq.TTS(voice="Cheyenne-PlayAI"),
        chat_ctx=initial_ctx,
    )

    @agent.on("metrics_collected")
    def _on_metrics_collected(mtrcs: metrics.AgentMetrics):
        metrics.log_metrics(mtrcs)

    agent.start(ctx.room)
    await agent.say("Hi, how's is going today?", allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            agent_name="groq-agent",
        )
    )
