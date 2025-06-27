import { StateGraph, StateGraphArgs } from "@langchain/langgraph";
import { BaseMessage } from "@langchain/core/messages";
import { TavilySearchResults } from "@langchain/community/tools/tavily_search";
import { ChatOpenAI } from "@langchain/openai";
import { ChatAnthropic } from "@langchain/anthropic";
import dotenv from "dotenv";

dotenv.config();

// Define the state interface
export interface PersonalityState {
  personName: string;
  tweets: any[];
  otherContent: any[];
  dataSufficient: boolean;
  searchAttempts: number;
  response: string;
}

// Create the graph with state
export const graphState: StateGraphArgs<PersonalityState>["channels"] = {
  personName: {
    value: (x: string, y?: string) => y ?? x,
    default: () => "",
  },
  tweets: {
    value: (x: any[], y?: any[]) => y ?? x,
    default: () => [],
  },
  otherContent: {
    value: (x: any[], y?: any[]) => y ?? x,
    default: () => [],
  },
  dataSufficient: {
    value: (x: boolean, y?: boolean) => y ?? x,
    default: () => false,
  },
  searchAttempts: {
    value: (x: number, y?: number) => y ?? x,
    default: () => 0,
  },
  response: {
    value: (x: string, y?: string) => y ?? x,
    default: () => "",
  },
};

// Initialize tools and LLM
const tavily = new TavilySearchResults({
  maxResults: 20,
  apiKey: process.env.TAVILY_API_KEY,
});

// Initialize LLM (use OpenAI or Anthropic based on available API keys)
let llm: ChatOpenAI | ChatAnthropic;

if (process.env.OPENAI_API_KEY) {
  llm = new ChatOpenAI({
    modelName: "gpt-4",
    temperature: 0.7,
    apiKey: process.env.OPENAI_API_KEY,
  });
} else if (process.env.ANTHROPIC_API_KEY) {
  llm = new ChatAnthropic({
    modelName: "claude-3-sonnet-20240229",
    temperature: 0.7,
    apiKey: process.env.ANTHROPIC_API_KEY,
  });
} else {
  throw new Error("Either OPENAI_API_KEY or ANTHROPIC_API_KEY must be set");
}

// Node 1: Search recent tweets
export async function searchRecentTweets(state: PersonalityState) {
  const oneYearAgo = new Date();
  oneYearAgo.setFullYear(oneYearAgo.getFullYear() - 1);
  const dateString = oneYearAgo.toISOString().split('T')[0];
  
  const query = `${state.personName} tweets after:${dateString}`;
  
  try {
    const results = await tavily.invoke(query);
    return {
      tweets: Array.isArray(results) ? results : [],
      searchAttempts: state.searchAttempts + 1,
    };
  } catch (error) {
    console.error("Error searching tweets:", error);
    return {
      tweets: [],
      searchAttempts: state.searchAttempts + 1,
    };
  }
}

// Node 2: Evaluate data sufficiency
export async function evaluateData(state: PersonalityState) {
  const tweets = Array.isArray(state.tweets) ? state.tweets : [];
  const otherContent = Array.isArray(state.otherContent) ? state.otherContent : [];
  
  const totalContent = tweets.length + otherContent.length;
  const currentYear = new Date().getFullYear();
  const hasRecent = tweets.some((t: any) => {
    const tweetStr = JSON.stringify(t);
    return tweetStr.includes(String(currentYear)) || 
           tweetStr.includes(String(currentYear - 1));
  });
  
  const sufficient = totalContent >= 15 && hasRecent;
  
  return { dataSufficient: sufficient };
}

// Node 3: Search additional sources
export async function searchAdditionalSources(state: PersonalityState) {
  let query: string;
  
  switch (state.searchAttempts) {
    case 1:
      query = `${state.personName} interview podcast 2024`;
      break;
    case 2:
      query = `${state.personName} speech quotes recent`;
      break;
    default:
      query = `${state.personName} opinions views`;
  }
  
  try {
    const results = await tavily.invoke(query);
    const currentOtherContent = Array.isArray(state.otherContent) ? state.otherContent : [];
    
    return {
      otherContent: [...currentOtherContent, ...results],
      searchAttempts: state.searchAttempts + 1,
    };
  } catch (error) {
    console.error("Error searching additional sources:", error);
    return {
      otherContent: state.otherContent || [],
      searchAttempts: state.searchAttempts + 1,
    };
  }
}

// Node 4: Generate response with LLM
export async function generateResponse(state: PersonalityState, currentQuery?: string) {
  const allContent = [...state.tweets, ...state.otherContent];
  
  // Create a prompt based on the collected content
  const contentSummary = allContent
    .slice(0, 10) // Limit to first 10 items to avoid token limits
    .map((item: any) => {
      if (item.content) return item.content;
      if (item.snippet) return item.snippet;
      if (item.title) return item.title;
      return JSON.stringify(item);
    })
    .join('\n\n');

  const query = currentQuery || "Tell me about yourself";
  
  const prompt = `You are ${state.personName}. Based on the following content about you, respond in your authentic voice and style:

${contentSummary}

User asks: "${query}"

Respond as ${state.personName} would, using your typical communication style, vocabulary, and personality traits. Be conversational and engaging.`;

  try {
    const response = await llm.invoke(prompt);
    return {
      response: response.content as string,
    };
  } catch (error) {
    console.error("Error generating response:", error);
    return {
      response: `I'm sorry, I'm having trouble generating a response right now. This is ${state.personName} speaking.`,
    };
  }
}

// Define conditional routing
export function shouldSearchMore(state: PersonalityState): string {
  if (state.dataSufficient) {
    return "generate";
  } else if (state.searchAttempts < 4) {
    return "searchMore";
  } else {
    return "generate";
  }
}
