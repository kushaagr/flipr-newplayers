$(document).ready(function() {
    $('#send-button').click(function() {
        var userMessage = $('#user-message').val();
        if (userMessage.trim() !== '') {
            // Display user message
            $('#chat-area').append('<div class="user-message">' + userMessage + '</div>');
            $('#user-message').val('');

            // Send message to backend
            $.ajax({
                url: '/ask',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ content: userMessage }),
                success: function(response) {
                    // Display Gemini's response
                    $('#chat-area').append('<div class="gemini-message">' + response.response + '</div>');
                    // Scroll to the bottom of the chat area
                    $('#chat-area').scrollTop($('#chat-area')[0].scrollHeight);
                },
                error: function(error) {
                    console.error('Error:', error);
                    $('#chat-area').append('<div class="error-message">Error: ' + error.responseJSON.error + '</div>');
                    // Scroll to the bottom of the chat area
                    $('#chat-area').scrollTop($('#chat-area')[0].scrollHeight);
                }
            });
            // Scroll to the bottom of the chat area
            $('#chat-area').scrollTop($('#chat-area')[0].scrollHeight);
        }
    });
     // Scroll to the bottom of the chat area on page load
    $('#chat-area').scrollTop($('#chat-area')[0].scrollHeight);
});