// Global variable to store selected images
let selectedImages = [];

// Utility functions
function scrollToBottom() {
  const container = document.querySelector('.chat-messages');
  if (container) {
    container.scrollTop = container.scrollHeight;
  }
}

async function clearChat() {
  try {
    // Call the end session endpoint
    const response = await fetch("/end_session", {
      method: "POST",
    });
    
    if (response.ok) {
      // Clear any client-side state
      const messages = document.getElementById("messages");
      if (messages) {
        messages.innerHTML = "";
      }
      
      // Reload the page to start fresh
      location.reload();
    } else {
      console.error("Failed to end session");
    }
  } catch (error) {
    console.error("Error ending session:", error);
  }
}

// Text-to-Speech functionality
let ttsEnabled = false;

function toggleTTS() {
  ttsEnabled = !ttsEnabled;

  const btn = document.getElementById("tts-toggle");
  if (btn) {
    const icon = btn.querySelector("i");
    btn.setAttribute("aria-pressed", ttsEnabled);
    if (icon) {
      icon.className = ttsEnabled ? "fas fa-volume-up" : "fas fa-volume-mute";
    }
  }
}

function speakText(text) {
  if (!ttsEnabled || !window.speechSynthesis) return;

  const utter = new SpeechSynthesisUtterance(text);
  utter.lang = "el-GR"; // Greek language
  speechSynthesis.speak(utter);
}

// Main chat functionality
async function sendMessage(event) {
  event.preventDefault();

  const input = document.getElementById("userInput");
  const message = input.value.trim();
  if (!message) return;

  appendMessage("user", message);
  input.value = "";
  
  // Show typing indicator
  showTypingIndicator();

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });

    const data = await response.json();
    
    // Remove typing indicator before showing response
    removeTypingIndicator();
    
    appendMessage("bot", data.reply);
    scrollToBottom();
    
    if (ttsEnabled) {
      speakText(data.reply);
    }
  } catch (error) {
    console.error("Error sending message:", error);
    // Remove typing indicator in case of error
    removeTypingIndicator();
    appendMessage("bot", "Συγγνώμη, υπήρξε πρόβλημα. Παρακαλώ δοκιμάστε ξανά.");
  }
}

function appendMessage(sender, text) {
  const messages = document.getElementById("messages");
  const msg = document.createElement("div");
  msg.classList.add("message", sender);
  
  if (sender === "bot") {
    const messageContent = document.createElement("div");
    messageContent.classList.add("message-content");
    
    const img = document.createElement("img");
    img.src = "/static/images/images.png";
    img.alt = "Hellas Direct Agent";
    img.classList.add("agent-image");
    
    const textDiv = document.createElement("div");
    textDiv.textContent = text;
    textDiv.classList.add("message-text");
    
    messageContent.appendChild(img);
    messageContent.appendChild(textDiv);
    msg.appendChild(messageContent);
  } else {
    msg.textContent = text;
  }
  
  messages.appendChild(msg);
  scrollToBottom();
}

// Voice input functionality
let recognition;
let isListening = false;

function handleVoiceInput() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    alert("Your browser does not support Speech Recognition.");
    return;
  }

  const input = document.getElementById("userInput");
  const micBtn = document.querySelector(".voice-btn i");

  // Initialize once
  if (!recognition) {
    recognition = new SpeechRecognition();
    recognition.lang = "el-GR"; // Greek language
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      input.value = transcript;
      input.focus();
    };

    recognition.onerror = (event) => {
      console.error("Speech recognition error:", event.error);
      stopListening();
    };

    recognition.onend = () => {
      console.log("Voice recognition ended.");
      stopListening();
    };
  }

  // Toggle listening state
  if (!isListening) {
    recognition.start();
    isListening = true;
    toggleMicIcon(true);
    console.log("Voice recognition started. Speak now.");
  } else {
    recognition.stop(); // onend will handle cleanup
  }
}

function stopListening() {
  isListening = false;
  toggleMicIcon(false);
}

function toggleMicIcon(active) {
  const micBtn = document.querySelector(".voice-btn i");
  const wave = document.getElementById("wave");
  
  if (micBtn) {
    if (active) {
      micBtn.classList.remove("fa-microphone");
      micBtn.classList.add("fa-microphone-slash");
      if (wave) wave.style.display = "inline-block";
    } else {
      micBtn.classList.remove("fa-microphone-slash");
      micBtn.classList.add("fa-microphone");
      if (wave) wave.style.display = "none";
    }
  }
}

// Image upload functionality
function handleImageUpload() {
  const input = document.getElementById('imageInput');
  if (input) {
    input.click();
    
    input.onchange = async function(e) {
      const files = Array.from(e.target.files);
      if (files.length === 0) return;
      
      // Check if all files are images
      const invalidFiles = files.filter(file => !file.type.startsWith('image/'));
      if (invalidFiles.length > 0) {
        alert('Παρακαλώ επιλέξτε μόνο εικόνες.');
        return;
      }
      
      // Display image previews in chat
      files.forEach(file => {
        const reader = new FileReader();
        reader.onload = function(event) {
          const img = document.createElement('img');
          img.src = event.target.result;
          img.classList.add('chat-image');
          
          const messageDiv = document.createElement('div');
          messageDiv.classList.add('message', 'user');
          messageDiv.appendChild(img);
          
          document.getElementById('messages').appendChild(messageDiv);
          scrollToBottom();
        };
        reader.readAsDataURL(file);
      });
      
      // Show typing indicator while processing images
      showTypingIndicator();
      
      // Send images to server
      const formData = new FormData();
      files.forEach(file => {
        formData.append('images', file);
      });
      
      try {
        const response = await fetch("/upload_images", {
          method: "POST",
          body: formData,
        });
        
        const data = await response.json();
        
        // Remove typing indicator before showing response
        removeTypingIndicator();
        
        appendMessage("bot", data.reply);
        
        if (ttsEnabled) {
          speakText(data.reply);
        }
      } catch (error) {
        console.error("Error uploading images:", error);
        // Remove typing indicator in case of error
        removeTypingIndicator();
        appendMessage("bot", "Συγγνώμη, υπήρξε πρόβλημα με την ανάλυση των εικόνων.");
      }
      
      // Clear the input
      input.value = '';
    };
  }
}

// Theme and Lottie animation functionality
let lottieAnim;

document.addEventListener('DOMContentLoaded', () => {
  const themeToggle = document.getElementById('theme-toggle');
  
  if (themeToggle) {
    const icon = themeToggle.querySelector('i');
    
    // Initialize Lottie animation if container exists
    const lottieContainer = document.getElementById('lottie-background');
    if (lottieContainer && typeof lottie !== 'undefined') {
      lottieAnim = lottie.loadAnimation({
        container: lottieContainer,
        renderer: 'svg',
        loop: true,
        autoplay: true,
        path: 'https://assets.hellasdirect.gr/common/assets/5.11.76/images/website/lottie-animations/lottie-global-home-hero-lg.json'
      });
      
      // Wait for animation to load before updating color
      lottieAnim.addEventListener('DOMLoaded', () => {
        const savedTheme = localStorage.getItem('theme') || 'light';
        updateLottieColor(savedTheme === 'dark');
      });
    }

    // Check for saved theme preference
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme === 'dark');
    
    themeToggle.addEventListener('click', () => {
      const currentTheme = document.documentElement.getAttribute('data-theme');
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      
      document.documentElement.setAttribute('data-theme', newTheme);
      localStorage.setItem('theme', newTheme);
      updateThemeIcon(newTheme === 'dark');
      updateLottieColor(newTheme === 'dark');
    });
    
    function updateThemeIcon(isDark) {
      if (icon) {
        icon.className = isDark ? 'fas fa-sun' : 'fas fa-moon';
      }
    }

    function updateLottieColor(isDark) {
      const color = isDark ? '#FFFFFF' : '#000000';
      
      if (lottieAnim && lottieAnim.renderer) {
        try {
          lottieAnim.renderer.elements.forEach(element => {
            if (element && element.shape) {
              element.shape.paths.forEach(path => {
                if (path.c) {
                  path.c.k = color;
                }
              });
            }
          });
          lottieAnim.renderer.renderFrame(null);
        } catch (error) {
          console.log("Lottie color update failed:", error);
        }
      }
    }
  }
});

// Initialize chat when page loads
window.onload = async function() {
  try {
    const response = await fetch("/start_chat");
    const data = await response.json();
    
    if (data.chat_history && data.chat_history.length > 0) {
      // Display existing chat history
      displayChatHistory(data.chat_history);
    } else if (data.reply) {
      // Display initial message for new sessions
      appendMessage("bot", data.reply);
    }
  } catch (error) {
    console.error("Error starting chat:", error);
    appendMessage("bot", "Γεια σας! Πώς μπορώ να σας βοηθήσω;");
  }
};

function displayChatHistory(messages) {
  const messagesContainer = document.getElementById("messages");
  messagesContainer.innerHTML = "";
  
  messages.forEach(message => {
    const senderType = message.sender === "assistant" ? "bot" : message.sender;
    appendMessage(senderType, message.message);
  });
  
  scrollToBottom();
}

// Enhanced image upload with multiple file support
function handleImageSelection(event) {
  const files = Array.from(event.target.files);
  files.forEach(file => {
    if (file.type.startsWith('image/')) {
      selectedImages.push(file);
    }
  });
  
  updateImagePreview();
  updateImageButton();
  
  // Clear the file input so the same files can be selected again if needed
  event.target.value = '';
}

function updateImagePreview() {
  const container = document.getElementById('selectedImages');
  if (container) {
    container.innerHTML = '';
    
    selectedImages.forEach((file, index) => {
      const preview = document.createElement('div');
      preview.className = 'image-preview';
      
      const img = document.createElement('img');
      img.src = URL.createObjectURL(file);
      
      const removeBtn = document.createElement('button');
      removeBtn.className = 'remove-image';
      removeBtn.innerHTML = '×';
      removeBtn.onclick = () => removeImage(index);
      
      preview.appendChild(img);
      preview.appendChild(removeBtn);
      container.appendChild(preview);
    });
  }
}

function removeImage(index) {
  selectedImages.splice(index, 1);
  updateImagePreview();
  updateImageButton();
}

function clearSelectedImages() {
  selectedImages = [];
  updateImagePreview();
  updateImageButton();
}

function updateImageButton() {
  const button = document.getElementById('imageButton');
  if (button) {
    if (selectedImages.length > 0) {
      button.classList.add('has-images');
      button.innerHTML = `📷 ${selectedImages.length}`;
    } else {
      button.classList.remove('has-images');
      button.innerHTML = '📷';
    }
  }
}

async function sendImages() {
  if (selectedImages.length === 0) return;
  
  const formData = new FormData();
  selectedImages.forEach(file => {
    formData.append('images', file);
  });
  
  // Show what user is sending
  appendMessage("user", `📸 Uploading ${selectedImages.length} image${selectedImages.length > 1 ? 's' : ''}...`);
  
  // Clear selected images
  clearSelectedImages();
  
  // Show typing indicator
  showTypingIndicator();
  
  try {
    const response = await fetch("/upload_images", {
      method: "POST",
      body: formData,
    });
    
    const data = await response.json();
    
    // Remove typing indicator before showing response
    removeTypingIndicator();
    
    if (response.ok) {
      appendMessage("bot", data.reply);
      if (ttsEnabled) {
        speakText(data.reply);
      }
    } else {
      appendMessage("bot", data.reply || "Sorry, I encountered an error processing the images.");
    }
  } catch (error) {
    console.error("Error sending images:", error);
    // Remove typing indicator in case of error
    removeTypingIndicator();
    appendMessage("bot", "Sorry, I'm having trouble processing the images. Please try again.");
  }
}

// Typing indicator functions
function showTypingIndicator() {
  const messages = document.getElementById("messages");
  
  // Remove existing typing indicator if any
  removeTypingIndicator();
  
  // Create typing indicator
  const indicator = document.createElement("div");
  indicator.classList.add("typing-indicator");
  
  const messageContent = document.createElement("div");
  messageContent.classList.add("message-content");
  
  const img = document.createElement("img");
  img.src = "/static/images/images.png";
  img.alt = "Hellas Direct Agent";
  img.classList.add("agent-image");
  
  const dots = document.createElement("div");
  dots.classList.add("dots");
  
  // Add three dots
  for (let i = 0; i < 3; i++) {
    const dot = document.createElement("div");
    dot.classList.add("dot");
    dots.appendChild(dot);
  }
  
  messageContent.appendChild(img);
  messageContent.appendChild(dots);
  indicator.appendChild(messageContent);
  messages.appendChild(indicator);
  
  // Trigger reflow to ensure animation plays
  indicator.offsetHeight;
  indicator.classList.add("visible");
  
  scrollToBottom();
}

function removeTypingIndicator() {
  const indicator = document.querySelector(".typing-indicator");
  if (indicator) {
    indicator.remove();
  }
}