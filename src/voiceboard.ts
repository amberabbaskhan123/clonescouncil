import { StateGraph } from "@langchain/langgraph";
import { searchRecentTweets, evaluateData, searchAdditionalSources } from "./workflow";
import { generateConversationalResponse, conversationGraphState, ConversationState } from "./conversation";
import { BaseMessage } from "@langchain/core/messages";


// Create a Voiceboard class to manage conversations
export class Voiceboard {
    private personName: string;
    private app: any;
    private state: ConversationState;
    private initialized: boolean = false;
  
    constructor(personName: string) {
      this.personName = personName;
      this.state = {
        personName,
        tweets: [],
        otherContent: [],
        dataSufficient: false,
        searchAttempts: 0,
        response: "",
        conversationHistory: [],
        currentQuery: "",
        personalityContext: "",
      };
      
      // Build the workflow
      this.app = this.buildWorkflow();
    }
  
    private buildWorkflow() {
      const workflow = new StateGraph<ConversationState>({
        channels: conversationGraphState,
      });
  
      // Add all nodes (including previous ones)
      workflow.addNode("searchTweets", searchRecentTweets);
      workflow.addNode("evaluate", evaluateData);
      workflow.addNode("searchMore", searchAdditionalSources);
      workflow.addNode("generate", generateConversationalResponse);
  
      // Add edges (same as before)
      workflow.addEdge("searchTweets", "evaluate");
      workflow.addConditionalEdges(
        "evaluate",
        shouldSearchMore,
        {
          searchMore: "searchMore",
          generate: "generate",
        }
      );
      workflow.addEdge("searchMore", "evaluate");
      workflow.setEntryPoint("searchTweets");
  
      return workflow.compile();
    }
  
    // Initialize the voiceboard with personality data
    async initialize() {
      if (!this.initialized) {
        console.log(`Initializing voiceboard for ${this.personName}...`);
        this.state = await this.app.invoke(this.state);
        this.initialized = true;
        console.log(`Loaded ${this.state.tweets.length} tweets and ${this.state.otherContent.length} other sources`);
      }
    }
  
    // Have a conversation
    async chat(message: string): Promise<string> {
      if (!this.initialized) {
        await this.initialize();
      }
  
      // For subsequent messages, just run the generate node
      this.state.currentQuery = message;
      
      // Create a simple workflow just for generation
      const chatWorkflow = new StateGraph<ConversationState>({
        channels: conversationGraphState,
      });
      chatWorkflow.addNode("generate", generateConversationalResponse);
      chatWorkflow.setEntryPoint("generate");
      
      const chatApp = chatWorkflow.compile();
      this.state = await chatApp.invoke(this.state);
      
      return this.state.response;
    }
  
    // Get conversation history
    getHistory(): BaseMessage[] {
      return this.state.conversationHistory;
    }
  
    // Clear conversation but keep personality
    clearConversation() {
      this.state.conversationHistory = [];
      console.log("Conversation cleared, personality retained");
    }
  
    // Refresh personality data
    async refreshPersonality() {
      this.initialized = false;
      this.state.tweets = [];
      this.state.otherContent = [];
      this.state.searchAttempts = 0;
      await this.initialize();
    }
}
  
// Usage Example
async function runVoiceboard() {
    // Create a voiceboard for a specific person
    const elonBoard = new Voiceboard("Elon Musk");
    
    // Initialize (fetches tweets and content)
    await elonBoard.initialize();
    
    // Have a conversation
    console.log("\n--- Starting Conversation ---\n");
    
    let response = await elonBoard.chat("What do you think about the future of electric vehicles?");
    console.log("AI Elon:", response);
    
    response = await elonBoard.chat("But what about the infrastructure challenges?");
    console.log("\nAI Elon:", response);
    
    response = await elonBoard.chat("How does this connect to your Mars plans?");
    console.log("\nAI Elon:", response);
    
    // The conversation maintains context and personality!
}
  
// Interactive CLI version
import * as readline from 'readline';

async function interactiveVoiceboard(personName: string) {
const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
});

const voiceboard = new Voiceboard(personName);
await voiceboard.initialize();

console.log(`\n🎙️ Voiceboard initialized for ${personName}`);
console.log("Type 'exit' to quit, 'clear' to reset conversation\n");

const askQuestion = () => {
    rl.question('You: ', async (input) => {
    if (input.toLowerCase() === 'exit') {
        rl.close();
        return;
    }
    
    if (input.toLowerCase() === 'clear') {
        voiceboard.clearConversation();
        console.log("Conversation cleared!\n");
        askQuestion();
        return;
    }
    
    const response = await voiceboard.chat(input);
    console.log(`\n${personName}: ${response}\n`);
    askQuestion();
    });
};

askQuestion();
}

// Run the interactive version
interactiveVoiceboard("Elon Musk");