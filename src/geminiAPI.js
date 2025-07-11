const { GoogleGenerativeAI } = require('@google/generative-ai');

class GeminiAPI {
  constructor(apiKey) {
    this.apiKey = apiKey;
    this.isSimulated = false;
    
    // Check if API key is provided
    if (!apiKey || apiKey === 'your_gemini_api_key_here') {
      console.warn('No valid Gemini API key provided. Using simulated responses.');
      this.isSimulated = true;
    } else {
      try {
        this.genAI = new GoogleGenerativeAI(this.apiKey);
        this.model = this.genAI.getGenerativeModel({ model: 'gemini-pro' });
        console.log('Gemini API initialized with provided key');
      } catch (error) {
        console.error('Error initializing Gemini API:', error);
        this.isSimulated = true;
      }
    }
  }
  
  async getInterviewResponse(interviewText) {
    if (!interviewText || typeof interviewText !== 'string') {
      throw new Error('Invalid interview text');
    }
    
    // If we're in simulated mode, return a mock response
    if (this.isSimulated) {
      console.log('Using simulated Gemini response (no valid API key)');
      return this.getSimulatedResponse(interviewText);
    }
    
    try {
      const prompt = `
You are an expert interview coach. Based on the following interview question or conversation, 
provide a concise, professional response that would impress the interviewer.

If the text contains multiple speakers or a back-and-forth conversation, identify the most recent question 
or topic that needs addressing.

Interview text:
"""
${interviewText}
"""

Provide a response that demonstrates:
1. Clear understanding of the question/topic
2. Relevant experience and knowledge
3. Structured thinking
4. Positive attitude

Keep your response concise (3-5 sentences) but impactful. Focus on key points that would make the candidate stand out.
`;
      
      console.log('Sending request to Gemini API...');
      const result = await this.model.generateContent(prompt);
      const response = result.response;
      
      return response.text();
    } catch (error) {
      console.error('Error calling Gemini API:', error);
      
      // Fall back to simulated response if API call fails
      console.log('Falling back to simulated response due to API error');
      return this.getSimulatedResponse(interviewText);
    }
  }
  
  getSimulatedResponse(interviewText) {
    // Extract a potential question from the text
    const questionMatch = interviewText.match(/(?:\?|tell me about|describe|explain|how would you|what is|what are|why)/i);
    const hasQuestion = questionMatch !== null;
    
    // Simulated responses for demonstration purposes
    const simulatedResponses = [
      "I've successfully handled similar challenges by implementing a structured approach that focuses on prioritization, clear communication, and regular progress tracking. My experience has taught me the importance of both technical excellence and collaborative teamwork to ensure optimal results.",
      
      "My approach to problem-solving combines analytical thinking with creative solutions. I first break down complex issues into manageable components, then systematically address each while maintaining a holistic view. This methodology has consistently delivered successful outcomes in my previous roles.",
      
      "I believe effective leadership comes from a combination of clear vision, empathetic communication, and leading by example. Throughout my career, I've found that empowering team members while providing appropriate guidance creates an environment where innovation and productivity flourish naturally.",
      
      "Based on my experience with similar projects, I would approach this by first establishing clear requirements and success metrics, then developing a phased implementation plan with built-in feedback loops. This ensures we can deliver value quickly while remaining adaptable to changing needs.",
      
      "Technical challenges often require both depth of expertise and breadth of perspective. I've cultivated both through continuous learning and collaborative work across disciplines. This balanced approach has proven effective when tackling complex problems that require innovative solutions."
    ];
    
    // Simple logic to pick a response based on the input text
    const textLength = interviewText.length;
    const responseIndex = textLength % simulatedResponses.length;
    
    console.log(`Simulated response selected (index ${responseIndex})`);
    return simulatedResponses[responseIndex];
  }
  
  // Method to check API key validity
  async validateAPIKey() {
    if (this.isSimulated) {
      return { 
        valid: false, 
        error: "No valid API key provided. Using simulated responses.",
        simulated: true
      };
    }
    
    try {
      // Attempt a simple generation to check if the API key works
      const result = await this.model.generateContent('Test API key validity');
      return { valid: true };
    } catch (error) {
      console.error('API key validation error:', error);
      this.isSimulated = true;
      return { 
        valid: false, 
        error: error.message,
        simulated: true
      };
    }
  }
}

module.exports = GeminiAPI; 