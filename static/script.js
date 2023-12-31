document.getElementById('chat-form').addEventListener('submit', function (event) {
    event.preventDefault();
    var userInput = document.getElementById('user-input').value;
    document.getElementById('user-input').value = '';
  
    displayMessage('user', userInput);
  
    // Call your web API here with userInput
    // Example API call using fetch:
    fetch(`/qa?query=${encodeURIComponent(userInput)}`)
      .then(response => response.json())
      .then(data => {
        const botAnswer = marked.parse(data.answer);
        const sources = data.sources;
  
        displayMessage('bot', botAnswer);
  
        // Check if sources are available and display them
        if (Array.isArray(sources)) {
          displaySources(sources);
        }
      })
      .catch(error => {
        console.error('Error:', error);
      });
  });
  
  function displayMessage(sender, message) {
    var chatLog = document.getElementById('chat-log');
  
    var messageElement = document.createElement('div');
    messageElement.classList.add(sender === 'user' ? 'user-message' : 'bot-message');
    messageElement.innerHTML = message; // Use innerHTML instead of textContent
  
    chatLog.appendChild(messageElement);
  
    // Scroll to the bottom of the chat log
    chatLog.scrollTop = chatLog.scrollHeight;
  }
  
  function displaySources(sources) {
    const chatLog = document.getElementById('chat-log');
  
    const sourcesPanel = document.createElement('div');
    sourcesPanel.classList.add('sources-panel');
  
    const sourcesHeading = document.createElement('h4');
    sourcesHeading.classList.add('sources-heading');
    sourcesHeading.textContent = 'Sources';
  
    const sourcesList = document.createElement('ul');
    sourcesList.classList.add('sources-list');
  
    const uniqueSources = Array.from(new Set(sources)); // Get unique sources
  
    uniqueSources.forEach(source => {
      const sourceItem = document.createElement('li');
      sourceItem.innerHTML = marked.parse(source)
      sourcesList.appendChild(sourceItem);
    });
  
    sourcesPanel.appendChild(sourcesHeading);
    sourcesPanel.appendChild(sourcesList);
    chatLog.appendChild(sourcesPanel);
  
    // Scroll to the bottom of the chat log
    chatLog.scrollTop = chatLog.scrollHeight;
  }
  
  
  function isValidURL(url) {
    try {
      new URL(url);
      return true;
    } catch (error) {
      return false;
    }
  }
  
    
    // Add event listener to the reset button
  document.getElementById('reset-button').addEventListener('click', function () {
    resetChat();
    callResetAPI();
  });
  
  function resetChat() {
    document.getElementById('chat-log').innerHTML = ''; // Clear chat contents
  }
  
  function callResetAPI() {
    fetch('/reset')
      .then(response => {
        if (response.ok) {
          console.log('Chat reset successfully.');
        } else {
          console.error('Failed to reset chat.');
        }
      })
      .catch(error => {
        console.error('Error:', error);
      });
  }

  function resizeInput(input) {
    input.style.height = "auto"; // Reset the height to auto
    input.style.height = input.scrollHeight + "px"; // Set the height to match the content
    if (input.scrollWidth > input.offsetWidth) {
      input.style.height = input.scrollHeight + (input.scrollHeight - input.offsetHeight) + "px";
    }
  }

  window.addEventListener('DOMContentLoaded', function() {
    // Display the welcome message
    var welcomeMessage = "Welcome, this is your friendly combit DocBot :). How can I help you today?";
    displayMessage('bot', welcomeMessage);
  });