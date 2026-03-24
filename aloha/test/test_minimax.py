from openai import OpenAI

client = OpenAI(api_key='sk-cp-_Qe8NJYog4n9mVCAxjfA6x3LHZ1Ot8hKAiEt732QKxkWga6T-NTRGqNUG9m4xdXqJ1A97rJbSBP8vv3_Df8qZPdO9Z40d3LbALY1U_cIDS7w2kCgE6UtZ_k',
                base_url='https://api.minimaxi.com/v1')

response = client.chat.completions.create(
    model="MiniMax-M2.7",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hi, how are you?"},
    ],
    # 设置 reasoning_split=True 将思考内容分离到 reasoning_details 字段
    extra_body={"reasoning_split": True},
)

print(f"Thinking:\n{response.choices[0].message.reasoning_details[0]['text']}\n")
print(f"Text:\n{response.choices[0].message.content}\n")