/**
 * app.js: JS code for the adk-streaming sample app.
 */

/**
 * WebSocket handling
 */

// Global variables
let sessionId = null;
let ws_url = null;
let websocket = null;
let is_audio = false;
let currentMessageId = null; // Track the current message ID during a conversation turn
let currentUserId = null; // Current user ID

// Generate random session ID for each conversation
// Now that we have ZepMemoryService, we don't need deterministic session IDs
function generateRandomSessionId() {
  return 'session_' + Math.random().toString(36).substr(2, 16) + '_' + Date.now().toString(36);
}

// Initialize session ID with user ID
async function initializeSession(userId = null) {
  try {
    // Generate a new random session ID for each conversation
    sessionId = generateRandomSessionId();
    // Include user_id in the WebSocket URL if provided
    const userParam = userId ? `&user_id=${encodeURIComponent(userId)}` : '';
    ws_url = "ws://" + window.location.host + "/ws/" + sessionId + "?is_audio=false" + userParam;
    console.log(`New session ID generated: ${sessionId}${userId ? ` for user: ${userId}` : ''}`);
    return true;
  } catch (error) {
    console.error('Failed to initialize session:', error);
    // Fallback to simpler random session ID
    sessionId = 'fallback_' + Math.random().toString().substring(2);
    const userParam = userId ? `&user_id=${encodeURIComponent(userId)}` : '';
    ws_url = "ws://" + window.location.host + "/ws/" + sessionId + "?is_audio=false" + userParam;
    return false;
  }
}

// Get DOM elements
const messageForm = document.getElementById("messageForm");
const messageInput = document.getElementById("message");
const messagesDiv = document.getElementById("messages");
const statusDot = document.getElementById("status-dot");
const connectionStatus = document.getElementById("connection-status");
const typingIndicator = document.getElementById("typing-indicator");
const startAudioButton = document.getElementById("startAudioButton");
const stopAudioButton = document.getElementById("stopAudioButton");
const recordingStatus = document.getElementById("recording-status");
const attachButton = document.getElementById("attachButton");
const fileInput = document.getElementById("fileInput");
const attachedFilesContainer = document.getElementById("attachedFiles");

// File attachment variables
let attachedFiles = [];

// File attachment functionality
attachButton.addEventListener("click", () => {
  fileInput.click();
});

fileInput.addEventListener("change", (event) => {
  const files = Array.from(event.target.files);
  files.forEach(file => {
    if (!attachedFiles.find(f => f.name === file.name && f.size === file.size)) {
      attachedFiles.push(file);
    }
  });
  updateAttachedFilesDisplay();
  // Reset file input to allow selecting the same file again
  fileInput.value = '';
});

function updateAttachedFilesDisplay() {
  if (attachedFiles.length === 0) {
    attachedFilesContainer.classList.remove("has-files");
    attachedFilesContainer.innerHTML = '';
    return;
  }

  attachedFilesContainer.classList.add("has-files");
  attachedFilesContainer.innerHTML = attachedFiles.map((file, index) => {
    const fileIcon = getFileIcon(file.type, file.name);
    const fileSize = formatFileSize(file.size);
    return `
      <div class="attached-file">
        <i class="file-icon ${fileIcon}"></i>
        <span class="file-name">${file.name}</span>
        <span class="file-size">${fileSize}</span>
        <button type="button" class="remove-file" data-index="${index}">
          <i class="fas fa-times"></i>
        </button>
      </div>
    `;
  }).join('');

  // Add event listeners for remove buttons
  attachedFilesContainer.querySelectorAll('.remove-file').forEach(button => {
    button.addEventListener('click', (e) => {
      const index = parseInt(e.currentTarget.dataset.index);
      attachedFiles.splice(index, 1);
      updateAttachedFilesDisplay();
    });
  });
}

function getFileIcon(mimeType, fileName) {
  const ext = fileName.split('.').pop().toLowerCase();

  if (mimeType.startsWith('image/')) {
    return 'fas fa-image';
  } else if (ext === 'pdf') {
    return 'fas fa-file-pdf';
  } else if (ext === 'docx' || ext === 'doc') {
    return 'fas fa-file-word';
  } else if (ext === 'txt') {
    return 'fas fa-file-alt';
  } else {
    return 'fas fa-file';
  }
}

function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

async function uploadFiles() {
  if (attachedFiles.length === 0) return [];

  const uploadedFiles = [];

  for (const file of attachedFiles) {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/upload', {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        const result = await response.json();
        uploadedFiles.push({
          filename: result.filename,
          original_name: file.name,
          mime_type: file.type,
          size: file.size
        });
      } else {
        console.error('Failed to upload file:', file.name);
      }
    } catch (error) {
      console.error('Error uploading file:', file.name, error);
    }
  }

  return uploadedFiles;
}

// WebSocket handlers
function connectWebsocket() {
  // Connect websocket - ws_url already contains all necessary parameters
  websocket = new WebSocket(ws_url);

  // Handle connection open
  websocket.onopen = function () {
    // Connection opened messages
    console.log("WebSocket connection opened.");
    connectionStatus.textContent = "Connected";
    statusDot.classList.add("connected");

    // Enable the Send button
    document.getElementById("sendButton").disabled = false;
    addSubmitHandler();
  };

  // Handle incoming messages
  websocket.onmessage = function (event) {
    // Parse the incoming message
    const message_from_server = JSON.parse(event.data);
    console.log("[AGENT TO CLIENT] ", message_from_server);

    // Show typing indicator for first message in a response sequence,
    // but not for turn_complete messages
    if (
      !message_from_server.turn_complete &&
      (message_from_server.mime_type === "text/plain" ||
        message_from_server.mime_type === "audio/pcm")
    ) {
      typingIndicator.classList.add("visible");
    }

    // Check if the turn is complete
    if (
      message_from_server.turn_complete &&
      message_from_server.turn_complete === true
    ) {
      // Reset currentMessageId to ensure the next message gets a new element
      currentMessageId = null;
      typingIndicator.classList.remove("visible");
      return;
    }

    // If it's audio, play it
    if (message_from_server.mime_type === "audio/pcm" && audioPlayerNode) {
      audioPlayerNode.port.postMessage(base64ToArray(message_from_server.data));

      // If we have an existing message element for this turn, add audio icon if needed
      if (currentMessageId) {
        const messageElem = document.getElementById(currentMessageId);
        if (
          messageElem &&
          !messageElem.querySelector(".audio-icon") &&
          is_audio
        ) {
          const audioIcon = document.createElement("span");
          audioIcon.className = "audio-icon";
          messageElem.prepend(audioIcon);
        }
      }
    }

    // Handle text messages
    if (message_from_server.mime_type === "text/plain") {
      // Hide typing indicator
      typingIndicator.classList.remove("visible");

      const role = message_from_server.role || "model";

      // If we already have a message element for this turn, append to it
      if (currentMessageId && role === "model") {
        const existingMessage = document.getElementById(currentMessageId);
        if (existingMessage) {
          // Append the text without adding extra spaces
          // Use a span element to maintain proper text flow
          const textNode = document.createTextNode(message_from_server.data);
          existingMessage.appendChild(textNode);

          // Scroll to the bottom
          messagesDiv.scrollTop = messagesDiv.scrollHeight;
          return;
        }
      }

      // Create a new message element if it's a new turn or user message
      const messageId = Math.random().toString(36).substring(7);
      const messageElem = document.createElement("p");
      messageElem.id = messageId;

      // Set class based on role
      messageElem.className =
        role === "user" ? "user-message" : "agent-message";

      // Add audio icon for model messages if audio is enabled
      if (is_audio && role === "model") {
        const audioIcon = document.createElement("span");
        audioIcon.className = "audio-icon";
        messageElem.appendChild(audioIcon);
      }

      // Add the text content
      messageElem.appendChild(
        document.createTextNode(message_from_server.data)
      );

      // Add the message to the DOM
      messagesDiv.appendChild(messageElem);

      // Remember the ID of this message for subsequent responses in this turn
      if (role === "model") {
        currentMessageId = messageId;
      }

      // Scroll to the bottom
      messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
  };

  // Handle connection close
  websocket.onclose = function () {
    console.log("WebSocket connection closed.");
    document.getElementById("sendButton").disabled = true;
    connectionStatus.textContent = "Disconnected. Reconnecting...";
    statusDot.classList.remove("connected");
    typingIndicator.classList.remove("visible");
    setTimeout(function () {
      console.log("Reconnecting...");
      connectWebsocket();
    }, 5000);
  };

  websocket.onerror = function (e) {
    console.log("WebSocket error: ", e);
    connectionStatus.textContent = "Connection error";
    statusDot.classList.remove("connected");
    typingIndicator.classList.remove("visible");
  };
}

// Initialize the application
async function initializeApp(userId = null) {
  currentUserId = userId;
  await initializeSession(userId);
  connectWebsocket();
}

// Make initializeApp available globally for the landing page
window.initializeApp = initializeApp;

// Don't auto-start the application anymore - wait for user ID input
// The landing page will call initializeApp when ready

// Change audio mode without reconnecting
async function changeAudioMode(enableAudio) {
  if (websocket && websocket.readyState === WebSocket.OPEN) {
    const modeMessage = {
      mime_type: "application/mode-change",
      mode: enableAudio ? "audio" : "text"
    };

    // Send mode change request
    sendMessage(modeMessage);

    // Set the audio mode flag
    is_audio = enableAudio;

    // Add or remove audio styling class
    if (enableAudio) {
      messagesDiv.classList.add("audio-enabled");
    } else {
      messagesDiv.classList.remove("audio-enabled");
    }

    console.log(`Changed to ${enableAudio ? 'audio' : 'text'} mode`);
    return true;
  }
  return false;
}

// Add submit handler to the form
function addSubmitHandler() {
  messageForm.onsubmit = async function (e) {
    e.preventDefault();
    const message = messageInput.value;
    const hasFiles = attachedFiles.length > 0;

    if (message || hasFiles) {
      // Upload files first if any
      let uploadedFiles = [];
      if (hasFiles) {
        uploadedFiles = await uploadFiles();
      }

      // Display user message
      const p = document.createElement("p");
      p.textContent = message || "(Files attached)";
      p.className = "user-message";
      messagesDiv.appendChild(p);

      // Show attached files in the message if any
      if (uploadedFiles.length > 0) {
        const filesList = document.createElement("div");
        filesList.className = "message-files";
        filesList.innerHTML = uploadedFiles.map(file => `
          <div class="message-file">
            <i class="${getFileIcon(file.mime_type, file.original_name)}"></i>
            <span>${file.original_name}</span>
          </div>
        `).join('');
        messagesDiv.appendChild(filesList);
      }

      messageInput.value = "";

      // Clear attached files
      attachedFiles = [];
      updateAttachedFilesDisplay();

      // Show typing indicator after sending message
      typingIndicator.classList.add("visible");

      // Send message with file information
      const messageData = {
        mime_type: "text/plain",
        data: message || "",
        role: "user",
      };

      // Add file information if files were uploaded
      if (uploadedFiles.length > 0) {
        messageData.uploaded_files = uploadedFiles;
      }

      sendMessage(messageData);
      console.log("[CLIENT TO AGENT] " + message);
      // Scroll down to the bottom of the messagesDiv
      messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
    return false;
  };
}

// Send a message to the server as a JSON string
function sendMessage(message) {
  if (websocket && websocket.readyState == WebSocket.OPEN) {
    const messageJson = JSON.stringify(message);
    websocket.send(messageJson);
  }
}

// Decode Base64 data to Array
function base64ToArray(base64) {
  const binaryString = window.atob(base64);
  const len = binaryString.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes.buffer;
}

/**
 * Audio handling
 */

let audioPlayerNode;
let audioPlayerContext;
let audioRecorderNode;
let audioRecorderContext;
let micStream;
let isRecording = false;

// Import the audio worklets
import { startAudioPlayerWorklet } from "./audio-player.js";
import { startAudioRecorderWorklet } from "./audio-recorder.js";

// Start audio
function startAudio() {
  // Start audio output
  startAudioPlayerWorklet().then(([node, ctx]) => {
    audioPlayerNode = node;
    audioPlayerContext = ctx;
  });
  // Start audio input
  startAudioRecorderWorklet(audioRecorderHandler).then(
    ([node, ctx, stream]) => {
      audioRecorderNode = node;
      audioRecorderContext = ctx;
      micStream = stream;
      isRecording = true;
    }
  );
}

// Stop audio recording
function stopAudio() {
  if (audioRecorderNode) {
    audioRecorderNode.disconnect();
    audioRecorderNode = null;
  }

  if (audioRecorderContext) {
    audioRecorderContext
      .close()
      .catch((err) => console.error("Error closing audio context:", err));
    audioRecorderContext = null;
  }

  if (micStream) {
    micStream.getTracks().forEach((track) => track.stop());
    micStream = null;
  }

  isRecording = false;
}

// Start the audio only when the user clicked the button
// (due to the gesture requirement for the Web Audio API)
startAudioButton.addEventListener("click", () => {
  startAudioButton.disabled = true;
  startAudioButton.innerHTML = '<i class="fas fa-microphone-slash"></i>';
  startAudioButton.classList.add("recording");
  startAudioButton.style.display = "none";
  stopAudioButton.style.display = "inline-block";
  recordingStatus.classList.add("active");
  startAudio();

  // Change to audio mode without reconnecting
  changeAudioMode(true);
});

// Stop audio recording when stop button is clicked
stopAudioButton.addEventListener("click", () => {
  stopAudio();
  stopAudioButton.style.display = "none";
  startAudioButton.style.display = "inline-block";
  startAudioButton.disabled = false;
  startAudioButton.innerHTML = '<i class="fas fa-microphone"></i>';
  startAudioButton.classList.remove("recording");
  recordingStatus.classList.remove("active");

  // Change to text mode without reconnecting
  changeAudioMode(false);
});

// Audio recorder handler
function audioRecorderHandler(pcmData) {
  // Only send data if we're still recording
  if (!isRecording) return;

  // Send the pcm data as base64
  sendMessage({
    mime_type: "audio/pcm",
    data: arrayBufferToBase64(pcmData),
  });

  // Log every few samples to avoid flooding the console
  if (Math.random() < 0.01) {
    // Only log ~1% of audio chunks
    console.log("[CLIENT TO AGENT] sent audio data");
  }
}

// Encode an array buffer with Base64
function arrayBufferToBase64(buffer) {
  let binary = "";
  const bytes = new Uint8Array(buffer);
  const len = bytes.byteLength;
  for (let i = 0; i < len; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return window.btoa(binary);
}
