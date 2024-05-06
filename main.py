from flask import Flask, request, jsonify, Response
from flask_cors import CORS

from zhipuai import ZhipuAI

import os

class WenTongZhiDa:
    def __init__(self):
        self.clientInit()
        if not os.path.exists("files"):
            os.makedirs("files")
        else:
            for file in os.listdir("files"):
                os.remove("files/" + file)

        if not os.path.exists("audios"):
            os.makedirs("audios")
        else:
            for file in os.listdir("audios"):
                os.remove("audios/" + file)

    def clientInit(self):
        self.client = ZhipuAI(api_key="a00cd208094df8a00c49b37b63ddbd05.ygWgeUVw5qkMfUIE")
    
    def getFilesContent(self):
        content = ""
        for file in os.listdir("files"):
            with open(file, 'r') as f:
                content += "文件名: " + file + "\n"
                # 根据后缀名判断文件类型
                if file.endswith('.txt'):
                    content += f.read() + "\n"
                elif file.endswith('.pdf'):
                    import PyPDF2
                    pdf = PyPDF2.PdfReader(file)
                    for page in pdf.pages:
                        content += page.extract_text() + "\n"
                elif file.endswith('.docx'):
                    import docx
                    doc = docx.Document(file)
                    for para in doc.paragraphs:
                        content += para.text + "\n"
            
        return content
    
    def get_knowledge_prompt(self):
        prompt = "你现在拥有的知识库包含你自带的知识库" \
                 "\"\"\"\n{{knowledge}}\"\"\"\n" 
        filesContent = self.getFilesContent()
        if filesContent:
            prompt += "和用户上传的文件" \
                      "\"\"\"\n" \
                      f"{filesContent}" \
                      "\"\"\"\n"
        else:
            prompt += "当前没有用户上传的文件。\n"
        prompt += "这些知识仅供参考，你可以根据用户的提问自由选择是否使用这些知识。\n"
        return prompt
    
    def first_prompt_template(self):
        prompt = "你的身份是" \
                 "\"\"\"\n" \
                 "你是一个名为“文通智答”的文档查阅助手，你的功能是根据用户的提问从文档中提取出对应的信息，并做出回答。\n" \
                 "\"\"\"\n" \
                 "请根据用户的输入" \
                 "\"\"\"\n{{question}}\n\"\"\"\n" \
                 "生成一个 JSON 格式的输出，其中包含以下键:\n" \
                 "\"\"\"\n" \
                 "user_question: 一个字符串，表示用户的提问。\n" \
                 "user_is_greeting: 0或1，表示用户的输入是否是问候语或者是关于你的身份的提问。\n" \
                 "user_is_question_about_knowledge: 0或1，表示用户的输入是否需要某领域的知识来解答。\n" \
                 "need_image: 0或1，表示回答中是否需要包含图片。\n" \
                 "\"\"\"\n" \
                 "只需要输出 JSON 格式的回答，不需要包含额外的信息。\n"
        prompt += self.get_knowledge_prompt()
        return prompt
    
    def get_greeting_prompt(self, question):
        prompt = "你的身份是" \
                 "\"\"\"\n" \
                 "你是一个名为“文通智答”的文档查阅助手，你的功能是根据用户的提问从文档中提取出对应的信息，并做出回答。\n" \
                 "\"\"\"\n" \
                 "请你以\"文通智答\"的身份回答用户的问题" \
                 "\"\"\"\n" + question + "\n\"\"\"\n" \
                 "不要复述问题，直接开始回答。\n"
        return prompt
    
    def get_question_prompt(self, question):
        prompt = "你的身份是" \
                 "\"\"\"\n" \
                 "你是一个名为“文通智答”的文档查阅助手，你的功能是根据用户的提问从文档中提取出对应的信息，并做出回答，也可以根据用户的需求以及文档知识生成图片。\n" \
                 "\"\"\"\n" \
                 "请根据用户的问题" \
                 "\"\"\"\n{{question}}\n\"\"\"\n" \
                 "在给定的知识库中寻找答案，如果找到答案，就根据知识库中的知识回答，如果知识库中找不到答案，就根据自己的知识回答问题，并告诉用户回答不是来自文档。\n" \
                 "不要复述问题，直接开始回答。\n"
        prompt += self.get_knowledge_prompt()
        return prompt
    
    def get_image_prompt(self, question):
        prompt = "你的身份是" \
                 "\"\"\"\n" \
                 "你是一个名为“文通智答”的文档查阅助手，你的功能是根据用户的提问从文档中提取出对应的信息，并做出回答，也可以根据用户的需求以及文档知识生成图片。\n" \
                 "\"\"\"\n" \
                 "请根据用户的生成图片的需求" \
                 "\"\"\"\n" + question + "\n\"\"\"\n" \
                 "以及已有的知识库中的知识生成用于生成图片的提示词，否则为空。提示词要求采用精确、具体的视觉描述而非抽象概念。明确、清晰的结构化提示词可以创造出更高质量的图像。主体: 人、动物、建筑、物体等；媒介: 照片、绘画、插图、雕塑、涂鸦等；环境: 竹林、荷塘、沙漠、月球上、水下等；光线: 自然光、体积光、霓虹灯、工作室灯等；颜色: 单色、复色、彩虹色、柔和色等；情绪 : 开心、生气、悲伤、惊讶等；构图/角度: 肖像、特写、侧脸图、航拍图等。" \
                 "不要复述问题，直接开始回答。\n"
        prompt += self.get_knowledge_prompt()
        return prompt
    
    def get_image_prompt_prompt(self, prompt):
        prompt = "你的身份是" \
                 "\"\"\"\n" \
                 "你是一个名为“文通智答”的文档查阅助手，你的功能是根据用户的提问从文档中提取出对应的信息，并做出回答，也可以根据用户的需求以及文档知识生成图片。\n" \
                 "\"\"\"\n" \
                 "以下是用于生成图片的提示词" \
                 "\"\"\"\n" + prompt + "\n\"\"\"\n" \
                 "现在图片已经生成好了，你只需要告诉用户以下是你根据用户需求生成的图片，并简要地描述图片的内容。\n" \
                 "不要复述，直接开始回答。\n"
        prompt += self.get_knowledge_prompt()
        return prompt

    def chatbot(self, message):
        response = self.client.chat.completions.create(
            model="glm-4",
            messages=[
                {"role": "user", "content": message},
            ],
            tools=[
                {
                    "type": "retrieval",
                    "retrieval": {
                        "knowledge_id": "1784136662398517248",
                        "prompt_template": self.first_prompt_template() 
                    }
                }
            ],
        )

        print(response.choices[0].message.content)
        
        json_str = response.choices[0].message.content[7:-3]
        json_dict = eval(json_str)

        need_image = True if json_dict['need_image'] else False

        if json_dict['user_is_greeting'] and not json_dict['user_is_question_about_knowledge']:
            response1 = self.client.chat.completions.create(
                model="glm-4",
                messages=[
                    {"role": "user", "content": self.get_greeting_prompt(json_dict['user_question'])},
                ],
                stream=True
            )
            return need_image, "", response1
        else:
            if need_image:
                prompt_template = self.get_image_prompt(json_dict['user_question'])
            else:
                prompt_template = self.get_question_prompt(json_dict['user_question'])

            response1 = self.client.chat.completions.create(
                model="glm-4",
                messages=[
                    {"role": "user", "content": message},
                ],
                tools=[
                    {
                        "type": "retrieval",
                        "retrieval": {
                            "knowledge_id": "1784136662398517248",
                            "prompt_template": prompt_template
                        }
                    }
                ],
                stream=not need_image
            )
            
            if not need_image:
                return need_image, "", response1
            else:
                image_response = self.client.images.generations(
                    model="cogview-3",
                    prompt=response1.choices[0].message.content,
                )
                print(image_response.data[0].url)
                response2 = self.client.chat.completions.create(
                    model="glm-4",
                    messages=[
                        {"role": "user", "content": self.get_image_prompt_prompt(response1.choices[0].message.content)},
                    ],
                    stream=True
                )
                return need_image, image_response.data[0].url, response2

    def upload_file(self, files):
        for file in files:
            file.save("files/" + file.filename)

app = Flask(__name__)
CORS(app)

ai = WenTongZhiDa()

def send_message(message):
    need_image, image_url, response = ai.chatbot(message)

    print(need_image)

    def generate():
        if need_image:
            yield f"\"{image_url}\""
        else:
            yield f"\"no image\""
        for chunk in response:
            yield chunk.choices[0].delta.content

    return Response(generate(), mimetype='text/event-stream')

@app.route('/chatbot/audio', methods=['POST'])
def chatbot_audio_route():
    if 'file' not in request.files:
        return 'No file part', 400
    
    file = request.files['file']

    filename = file.filename
    file_path = f'audios/{filename}'
    file.save(file_path)

    from pydub import AudioSegment
    audio = AudioSegment.from_file(file_path)
    wave_file_path = file_path.rsplit('.', 1)[0] + '.wav'
    audio.export(wave_file_path, format='wav')

    import speech_recognition as sr

    r = sr.Recognizer()
    with sr.AudioFile(wave_file_path) as source:
        audio = r.record(source)
        os.environ['HTTP_PROXY'] = os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:1087'
        message = r.recognize_google(audio, language='zh-CN')
        return send_message(message)

@app.route('/chatbot', methods=['POST'])
def chatbot_route():
    data = request.json
    message = data['message']
    return send_message(message)

@app.route('/file/upload', methods=['POST'])
def file_upload():
    # 检查是否有文件被上传
    if not request.files:
        return jsonify({'message': 'No file part in the request'}), 400

    files = request.files.getlist('file')

    ai.upload_file(files)

    return jsonify({'message': 'File uploaded successfully'})

if __name__ == '__main__':
    app.run(port=5000)
