const API_KEY = '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'

// Initialize content area and input fields
document.addEventListener('DOMContentLoaded', function() {
    // Get elements after DOM is fully loaded
    const content = document.getElementById('content');
    const userInput = document.getElementById('userInput');
    
    // This line is updated to select any element that might be your send arrow
    // Adjust the selector based on your actual HTML structure - this covers several common possibilities
    const sendButton = document.querySelector('.send-button, .send-arrow, button[type="submit"], .fa-arrow-right, .send-icon');

    let isAnswerLoading = false;
    let answerSectionId = 0;

    // Add event listeners
    if (sendButton) {
        sendButton.addEventListener('click', function() {
            sendMessage();
        });
    } else {
        console.warn('Send button not found. Check your HTML structure and class names.');
    }

    userInput.addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            sendMessage();
        }
    });

    // Copy button functionality
    document.addEventListener('click', function(e) {
        if (e.target.closest('.copy-button') || e.target.closest('.fa-copy')) {
            const textToCopy = e.target.closest('.ai-prompt').querySelector('#first').textContent;
            navigator.clipboard.writeText(textToCopy).then(() => {
                alert('Text copied to clipboard');
            });
        }
    });

    // Function to send user message
    window.sendMessage = function() {
        const question = userInput.value.trim();

        if (question === '' || isAnswerLoading) return;

        // Add user message to chat
        addUserMessage(question);
        
        // Clear input field
        userInput.value = '';
        
        // Get AI response
        isAnswerLoading = true;
        answerSectionId++;
        
        // Add loading indicator
        addAnswerSection();
        
        // Fetch response from API
        getAnswer(question);
    };

    function addUserMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'up-down';

        // Using Font Awesome icon instead of image
        const userIcon = document.createElement('i');
        userIcon.className = 'fas fa-user-circle ai-logo'; // Using Font Awesome icon
        
        const messageText = document.createElement('p');
        messageText.textContent = message;
        messageText.id = 'second';
        
        messageDiv.appendChild(userIcon);
        messageDiv.appendChild(messageText);
        
        content.appendChild(messageDiv);
        scrollToBottom();
    }

    function addAnswerSection() {
        // Main container that will take the full width
        const sectionDiv = document.createElement('div');
        sectionDiv.className = 'ai-prompt';
        sectionDiv.id = `answer-${answerSectionId}`;
        sectionDiv.style.width = '100%';
        sectionDiv.style.display = 'flex';
        sectionDiv.style.flexDirection = 'column';
        
        // White background container that will stretch to fit all content
        const whiteContainer = document.createElement('div');
        whiteContainer.className = 'white-container';
        whiteContainer.style.backgroundColor = 'white';
        whiteContainer.style.borderRadius = '8px';
        whiteContainer.style.padding = '15px';
        whiteContainer.style.width = '100%';
        whiteContainer.style.boxShadow = '0 2px 5px rgba(0,0,0,0.1)';
        whiteContainer.style.marginBottom = '10px';
        whiteContainer.style.position = 'relative'; // Added for positioning the copy button
        
        const upDiv = document.createElement('div');
        upDiv.className = 'up';
        upDiv.style.display = 'flex';
        upDiv.style.alignItems = 'flex-start';
        upDiv.style.width = '100%';
        
        const aiImg = document.createElement('img');
        aiImg.src = 'Images/logo1.png'; // Make sure this file exists
        aiImg.alt = 'ai-logo';
        aiImg.className = 'ai-logo';
        aiImg.style.marginRight = '10px';
        aiImg.style.flexShrink = '0';
        
        const loadingIndicator = document.createElement('p');
        loadingIndicator.id = 'first';
        loadingIndicator.innerHTML = getLoadingSvg();
        loadingIndicator.style.width = '100%';
        loadingIndicator.style.margin = '0';
        loadingIndicator.style.wordWrap = 'break-word';
        loadingIndicator.style.whiteSpace = 'pre-wrap';
        
        upDiv.appendChild(aiImg);
        upDiv.appendChild(loadingIndicator);
        
        // Create copy button inside the white container
        const copyButton = document.createElement('button');
        copyButton.className = 'copy-button';
        copyButton.innerHTML = '<i class="fa-solid fa-copy"></i>Copy';
        copyButton.style.position = 'absolute';
        copyButton.style.bottom = '10px';
        copyButton.style.right = '10px';
        copyButton.style.backgroundColor = '#601893'; // Purple like in your image
        copyButton.style.color = 'white';
        copyButton.style.border = 'none';
        copyButton.style.borderRadius = '4px';
        copyButton.style.padding = '5px 10px';
        copyButton.style.fontSize = '14px';
        copyButton.style.cursor = 'pointer';
        copyButton.style.display = 'flex';
        copyButton.style.alignItems = 'center';
        copyButton.style.gap = '5px';
        
        // Put the upDiv inside the white container
        whiteContainer.appendChild(upDiv);
        whiteContainer.appendChild(copyButton);
        
        // Add the white container to the main section
        sectionDiv.appendChild(whiteContainer);
        
        content.appendChild(sectionDiv);
        scrollToBottom();
    }

    function getAnswer(question) {
        fetch("https://openrouter.ai/api/v1/chat/completions", {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${API_KEY}`,
                "HTTP-Referer": window.location.href, // Uses current site URL
                "X-Title": "Bloom Chatbot", // Your site/app name
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                "model": "mistralai/mistral-small-3.1-24b-instruct:free",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": question
                            }
                        ]
                    }
                ]
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            const resultData = data.choices[0].message.content;
            updateAnswerSection(resultData);
        })
        .catch(error => {
            console.error('Error fetching data:', error);
            updateAnswerSection("Sorry, something went wrong. Please try again.");
        })
        .finally(() => {
            isAnswerLoading = false;
            scrollToBottom();
        });
    }

    function updateAnswerSection(message) {
        const answerSection = document.getElementById(`answer-${answerSectionId}`);
        if (answerSection) {
            const messageP = answerSection.querySelector('#first');
            if (messageP) {
                // Replace the loading animation with the actual message
                messageP.innerHTML = message;
                
                // Force the container to expand with the content
                const whiteContainer = answerSection.querySelector('.white-container');
                if (whiteContainer) {
                    whiteContainer.style.height = 'auto';
                    whiteContainer.style.width = '100%';
                    
                    // Add some bottom padding to prevent text from being covered by the copy button
                    whiteContainer.style.paddingBottom = '40px';
                }
            }
        }
    }

    function getLoadingSvg() {
        return `
            <svg style="height:25px;" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
                <circle fill="#601893" stroke="#601893" stroke-width="15" r="15" cx="40" cy="65">
                    <animate attributeName="cy" calcMode="spline" dur="2" values="65;135;65;" keySplines=".5 0 .5 1;.5 0 .5 1" repeatCount="indefinite" begin="-.4"></animate>
                </circle>
                <circle fill="#601893" stroke="#601893" stroke-width="15" r="15" cx="100" cy="65">
                    <animate attributeName="cy" calcMode="spline" dur="2" values="65;135;65;" keySplines=".5 0 .5 1;.5 0 .5 1" repeatCount="indefinite" begin="-.2"></animate>
                </circle>
                <circle fill="#601893" stroke="#601893" stroke-width="15" r="15" cx="160" cy="65">
                    <animate attributeName="cy" calcMode="spline" dur="2" values="65;135;65;" keySplines=".5 0 .5 1;.5 0 .5 1" repeatCount="indefinite" begin="0"></animate>
                </circle>
            </svg>
        `;
    }

    function scrollToBottom() {
        content.scrollTop = content.scrollHeight;
    }
});
