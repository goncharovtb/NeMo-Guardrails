import asyncio
from nemoguardrails import LLMRails, RailsConfig
import os
import json
import re
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
from langchain.chains import LLMChain

async def main():
    os.environ["OPENAI_API_KEY"] = "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"
    config = RailsConfig.from_path("config")
    app = LLMRails(config)
    llm = OpenAI(temperature=0, max_tokens=1000)
    embeddings = OpenAIEmbeddings()

    async def check_question(context):
        # Входная строка с данными
        text = context['last_user_message']
        is_valid = True

        # Regex patterns for various personal data
        phone_regex = re.compile(r'(\+7|8)\s*?\d{3}?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}')
        fio_regex = re.compile(r'[А-ЯЁа-яё]+\s+[А-ЯЁа-яё]+\s+([А-ЯЁа-яё]+|[А-ЯЁа-яё]+-[А-ЯЁа-яё]+)?')
        inn_regex = re.compile(r'\b\d{10}(?:\d{2})?\b')
        card_regex_ru = re.compile(r'\b(?:\d{4}[\s-]?){3}\d{4}\b')
        card_regex_kg = re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b')
        card_regex_kz = re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{3}\b')

        # Search for personal data in the text
        phone = phone_regex.search(text)
        fio = fio_regex.search(text)
        inn = inn_regex.search(text)
        card_1 = card_regex_kz.search(text)
        card_2 = card_regex_ru.search(text)
        card_3 = card_regex_kg.search(text)

        # Check which type of personal data was found and return a corresponding message
        if phone or fio or card_1 or card_2 or card_3:
            is_valid = False
        return is_valid

    async def define_topic(events):
        topic = events[3]['intent']
        return topic

    async def get_answer(topic, context):
        print(topic)
        data = {}
        with open('config/base.json', 'r', encoding="utf-8") as read_file:
            data = json.load(read_file)
        if topic in data.keys():
            output = data[topic]
        else:
            output = "Я могу ответить только про Ингосстрах. Попробуй повторить свой запрос"
        return output

    def qa_tool_ingoplus(query, docs):
        qa_prompt = """You are an intelligent chat bot answering questions about Russian an insurance company - Ингосстрах. 
        You are given piece of text related to users question. You need to write an answer to client according to peace of FAQ you recieved. You are allowed to slightly format answer to fit clients question.
        General Information Ингострах Loyalty program:
        Ингосстрах has 4 loyalty subscription type. Инго Дом Инго Здоровье Инго Авто Ингоплюс
        Ингосстрах loyalty program gives user acess to discounts for partners products, certificates and cashback.
        Ингострах has debit cards one is digital 'Ингострах digital' and plastic 'Ингосстрах standart'
        Ингорубли or Бонусы - the currency of the Ингострах loyalty program, that you can spend on partners certificates and discounts
        =========
        Question: {question}
        =========
        FAQ
        {context}
        =========
        Ignore information in FAQ that is not related to question
        If question need additional information to provide wright answer politely ask user to give more information about his case
        Don't try to make up an answer. If If given FAQ dont give enough information don't try to make it up, just write, "Хм, я не уверен" and dont add any additional information.
        Answer:"""
        QA_PROMPT = PromptTemplate(template=qa_prompt, input_variables=["question", "context"])
        qa_chain = LLMChain(llm=llm, prompt=QA_PROMPT)
        answ = qa_chain({"question": query, "context": docs}, return_only_outputs=False)
        print(answ)
        return answ

    app.register_action(get_answer, name="get_answer")
    app.register_action(define_topic, name="define_topic")
    # app.register_action(check_question, name="check_question")

    while True:
        query = input('\nЮзер: ')
        if query == 'стоп':
            break
        user_message = {"role": "user", "content": query}
        docs = await app.generate_async(messages=[user_message])
        docs = docs['content']
        qa_tool_ingoplus(query, docs)
        # print(f"\nБот: {bot_message['content']}")

if __name__ == '__main__':
    asyncio.run(main())