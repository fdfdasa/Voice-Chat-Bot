// Initialize Web Speech API objects
const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
const startBtn = document.getElementById('start-btn');
const stopBtn = document.getElementById('stop-btn');
const outputDiv = document.getElementById('output');

let isListening = false;  // Track if the recognition is active
let audioCache = [];  // Cache for storing audio data

// Speech Recognition settings
recognition.lang = 'vi-VN';
recognition.interimResults = false;
recognition.maxAlternatives = 1;

// Start button event listener
startBtn.addEventListener('click', (event) => {
    event.preventDefault(); // Prevent default behavior if needed
    if (!isListening) {
        recognition.start();  // Start listening
        isListening = true;
        startBtn.disabled = true;
        stopBtn.disabled = false;
        addMessage("Đang lắng nghe...");
    }
});

// Stop button event listener
stopBtn.addEventListener('click', (event) => {
    event.preventDefault(); // Prevent default behavior if needed
    if (isListening) {
        recognition.stop();  // Stop listening
        isListening = false;
        startBtn.disabled = false;
        stopBtn.disabled = true;
        addMessage("Đã dừng nghe.");
    }
});

// Listen for speech recognition results
recognition.onresult = (event) => {
    const you = event.results[0][0].transcript.toLowerCase();
    console.log('Bạn nói:', you);
    addMessage(`Bạn: ${you}`);
    audioCache.push(you);  // Cache the recognized text
    processText(you);

    // Optionally continue listening
    if (isListening) {
        recognition.start();  // Start listening again immediately
    }
};

// Handle recognition errors
recognition.onerror = (event) => {
    console.error('Recognition Error:', event.error);
    addMessage("Lỗi nhận diện giọng nói.");
    isListening = false;
    startBtn.disabled = false;
    stopBtn.disabled = true;
};

// Process the text and send it to the server
function processText(text) {
    fetch('http://localhost:3000/process-text', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text })
    })
    .then(response => response.json())
    .then(data => {
        const response = data.response;
        addMessage(`Trợ lý: ${response}`);
        speak(response);  // Convert text to speech
        // Save the data asynchronously
        return saveData(text, response);
    })
    .catch(error => {
        console.error('Error:', error);
        addMessage("Lỗi kết nối đến máy chủ.");
    });
}

// Speak the response using ResponsiveVoice
function speak(text) {
    responsiveVoice.speak(text, "Vietnamese Female");  // Use the Vietnamese female voice
}

// Add a message to the chat window
function addMessage(text) {
    const message = document.createElement('div');
    message.textContent = text;
    outputDiv.appendChild(message);
    outputDiv.scrollTop = outputDiv.scrollHeight;  // Scroll to the bottom of the chat
}

// Save the data asynchronously
function saveData(text, response) {
    return fetch('http://localhost:3000/save-data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            text: text,
            response: response
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Data saved:', data);
    })
    .catch(error => {
        console.error('Error:', error);
    });
}
