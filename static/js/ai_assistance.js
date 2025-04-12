$(document).ready(function () {
    $('#insights-box').click(function () {
      generateAIContent('insights', '#insights-content');
    });
  
    $('#budgeting-tips-box').click(function () {
      generateAIContent('budgeting_tips', '#budgeting-tips-content');
    });
  
    function generateAIContent(contentType, targetElement) {
      $(targetElement).text('Generating...');
  
      $.ajax({
        url: '/generate_ai_content',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ content_type: contentType }),
        success: function (response) {
          $(targetElement).html(response.response);
        },
        error: function (error) {
          console.error('Error:', error);
          $(targetElement).html('<div class="error-message">Error: ' + error.responseJSON.error + '</div>');
        }
      });
    }
  });
  
