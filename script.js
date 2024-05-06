function handleFileUpload() {
    var fileInput = document.getElementById('fileInput');
    var newFiles = fileInput.files;
    var uploadedFilesList = document.getElementById('uploadedFilesList');

    uploadedFilesList.innerHTML = '';

    var formData = new FormData();

    if (newFiles.length) {
        var fileListElement = document.createElement('ul');
        for (var file of newFiles) {
            var fileElement = document.createElement('li');
            fileElement.textContent = file.name;
            fileListElement.appendChild(fileElement);
            formData.append('file', file);
        }
        uploadedFilesList.appendChild(fileListElement);

        fetch('http://127.0.0.1:5000/file/upload', {
            method: 'POST',
            body: formData,
        })
    } else {
        uploadedFilesList.innerHTML = '<li>请先选择文件。</li>';
    }
}

var messages = document.querySelector('.messages');

function receiveResponse(response) {
    (() => {
        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');

        return reader.read().then(({ done, value }) => {  
            if (done) {
                return Promise.reject('No more data');
            }

            first = decoder.decode(value, { stream: true })

            // 获取第一个""之间的内容，作为图片的url，其后的内容作为文本
            const image_url = first.match(/"([^"]*)"/)[1]
            const need_image = image_url !== 'no image'
            const text = first.substring(first.indexOf('"') + image_url.length + 1, first.length - 1)

            const message = document.createElement('div');
            message.classList.add('message', 'bot-message');
            message.textContent = text;
            messages.appendChild(message);
            return reader.read().then(function processText({ done, value }) {
                if (done) {
                    return Promise.resolve({need_image: need_image, image_url: image_url});
                }
                
                message.textContent += decoder.decode(value, { stream: true });     
                messages.scrollTop = messages.scrollHeight;
                
                return reader.read().then(processText);
            }); 
        });
    })()
    .then(({ need_image, image_url }) => {
        if (need_image) {
            const message = document.createElement('div');
            message.classList.add('message', 'bot-message');
            messages.appendChild(message);
            const image = document.createElement('img');
            image.src = image_url;
            message.appendChild(image);
            messages.scrollTop = messages.scrollHeight;
        }
    })
}

function sendMessage() {
    var input = document.getElementById('message-input');

    if (input.value.trim() !== '') {
        // 添加用户的消息到聊天窗口
        var userMessage = document.createElement('div');
        userMessage.classList.add('message', 'user-message');
        userMessage.textContent = input.value;
        messages.appendChild(userMessage);
        messages.scrollTop = messages.scrollHeight;

        const data = {
            message: input.value,
            will_return_image: false
        };
        input.value = ''
        fetch('http://127.0.0.1:5000/chatbot', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        })
        .then(response => receiveResponse(response))
        .catch((error) => {
            console.error('Error:', error);
        });
    }
}

var promise = false;
var mediaRecorder = null;
var recordButton = document.getElementById('audio');
var chunks = [];
function recordAudio() {
    if (!promise) {
        navigator.mediaDevices.getUserMedia({ audio: true })
        .then(function(stream) {  
            promise = true;
            return stream;
        })
        .then(function(stream) {
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.ondataavailable = function(e) {
                chunks.push(e.data);
            };
            mediaRecorder.onstop = function(e) {
                var blob = new Blob(chunks, { 'type' : 'audio/ogg; codecs=opus' });
                chunks = [];
                var url = URL.createObjectURL(blob);
                var audio = document.createElement('audio');
                audio.controls = true;
                audio.src = url;
                var messages = document.querySelector('.messages');
                var message = document.createElement('div');
                message.classList.add('message', 'user-message');
                message.appendChild(audio);
                messages.appendChild(message);
                messages.scrollTop = messages.scrollHeight;

                // 上传音频文件，并获取音频转换后的文本
                var formData = new FormData();
                formData.append('file', blob);
                fetch('http://127.0.0.1:5000/chatbot/audio', {
                    method: 'POST',
                    body: formData,
                })
                .then(response => receiveResponse(response))
                .catch((error) => {
                    console.error('Error:', error);
                });
            };
            console.log('start recording');
            recordButton.textContent = '停止录音'
            mediaRecorder.start();
        })
        .catch(function(err) {
            console.log('The following error occurred: ' + err);
        });
    } else {
        mediaRecorder.stop();
        console.log('stop recording');
        recordButton.textContent = '录音'
        promise = false;
    }
}
        

document.getElementById('message-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});