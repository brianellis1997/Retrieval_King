import logging
from typing import Optional, List
from openai import OpenAI
from app.core import settings

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.query_rewriter_model = settings.OPENAI_MODEL_QUERY_REWRITER
        self.generator_model = settings.OPENAI_MODEL_GENERATOR

    def rewrite_query(self, query: str) -> dict:
        try:
            response = self.client.chat.completions.create(
                model=self.query_rewriter_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a query optimization assistant. "
                            "Analyze if the user's query is complex, vague, or would benefit from being broken down into multiple queries. "
                            "Respond with a JSON object containing: "
                            '{"should_rewrite": boolean, "rewritten_queries": [list of rewrites] or null}'
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Query: {query}"
                    }
                ],
                temperature=0.1,
                max_tokens=200
            )

            content = response.choices[0].message.content
            logger.debug(f"Query rewrite response: {content}")

            import json
            try:
                result = json.loads(content)
                return result
            except json.JSONDecodeError:
                return {"should_rewrite": False, "rewritten_queries": None}

        except Exception as e:
            logger.error(f"Failed to rewrite query: {e}")
            return {"should_rewrite": False, "rewritten_queries": None}

    def generate_response(
        self,
        query: str,
        contexts: List[str],
        use_inline_citations: bool = True
    ) -> str:
        try:
            context_str = "\n\n".join(
                [f"[{i+1}] {context}" for i, context in enumerate(contexts)]
            )

            system_prompt = (
                "You are a helpful assistant that answers questions based on provided contexts. "
                "Provide accurate, concise answers grounded in the contexts provided. "
            )

            if use_inline_citations:
                system_prompt += (
                    "When referencing information from a context, use inline citations like [1], [2], etc. "
                    "to indicate which context the information comes from."
                )

            response = self.client.chat.completions.create(
                model=self.generator_model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": f"Contexts:\n{context_str}\n\nQuestion: {query}"
                    }
                ],
                temperature=0.3,
                max_tokens=1000
            )

            answer = response.choices[0].message.content
            logger.debug(f"Generated response of length: {len(answer)}")
            return answer

        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            raise

    def generate_response_stream(
        self,
        query: str,
        contexts: List[str],
        use_inline_citations: bool = True
    ):
        try:
            context_str = "\n\n".join(
                [f"[{i+1}] {context}" for i, context in enumerate(contexts)]
            )

            system_prompt = (
                "You are a helpful assistant that answers questions based on provided contexts. "
                "Provide accurate, concise answers grounded in the contexts provided. "
            )

            if use_inline_citations:
                system_prompt += (
                    "When referencing information from a context, use inline citations like [1], [2], etc. "
                )

            stream = self.client.chat.completions.create(
                model=self.generator_model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": f"Contexts:\n{context_str}\n\nQuestion: {query}"
                    }
                ],
                temperature=0.3,
                max_tokens=1000,
                stream=True
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Failed to generate streaming response: {e}")
            raise

    def set_generator_model(self, model_name: str):
        self.generator_model = model_name
        logger.info(f"Generator model set to: {model_name}")

    def set_query_rewriter_model(self, model_name: str):
        self.query_rewriter_model = model_name
        logger.info(f"Query rewriter model set to: {model_name}")


llm_service = LLMService()
