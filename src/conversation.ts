import { ChatOpenAI } from "@langchain/openai";
import { HumanMessage, SystemMessage, AIMessage, BaseMessage } from "@langchain/core/messages";
import { StateGraphArgs } from "@langchain/langgraph";
import { PersonalityState, graphState } from "./workflow";

// Enhanced state to include conversation
export interface ConversationState extends PersonalityState {
  conversationHistory: BaseMessage[];
  currentQuery: string;
  personalityContext: string;
}

// Update the graph state
export const conversationGraphState: StateGraphArgs<ConversationState>["channels"] = {
  ...graphState, // Previous state definitions
  conversationHistory: {
    value: (x: BaseMessage[], y?: BaseMessage[]) => y ?? x,
    default: () => [],
  },
  currentQuery: {
    value: (x: string, y?: string) => y ?? x,
    default: () => "",
  },
  personalityContext: {
    value: (x: string, y?: string) => y ?? x,
    default: () => "",
  },
};

// Enhanced generate function that maintains conversation
export async function generateConversationalResponse(state: ConversationState) {
  const llm = new ChatOpenAI({
    modelName: "gpt-4",
    temperature: 0.7,
  });
  
  // Build personality context from collected content
  const allContent = [...state.tweets, ...state.otherContent];
  const personalityContext = allContent
    .slice(0, 15)
    .map(c => c.content || c.snippet || c.text)
    .join("\n\n");
  
  // Create the system message with personality
  const systemMessage = new SystemMessage(
    `You are mimicking the speaking style and personality of ${state.personName}. 
     
     Based on these examples of their speech and tweets:
     ${personalityContext}
     
     Important guidelines:
     - Match their vocabulary, tone, and speaking patterns
     - Use similar phrases and expressions they commonly use
     - Maintain their perspective on topics
     - Keep their energy level and communication style
     - If they use specific catchphrases or signatures, include them naturally
     
     Stay in character throughout the conversation.`
  );
  
  // Build messages array with history
  const messages: BaseMessage[] = [
    systemMessage,
    ...state.conversationHistory,
    new HumanMessage(state.currentQuery)
  ];
  
  // Generate response
  const response = await llm.invoke(messages);
  const aiResponse = response.content as string;
  
  // Update conversation history
  const updatedHistory = [
    ...state.conversationHistory,
    new HumanMessage(state.currentQuery),
    new AIMessage(aiResponse)
  ];
  
  return {
    response: aiResponse,
    conversationHistory: updatedHistory,
    personalityContext: personalityContext,
  };
}

