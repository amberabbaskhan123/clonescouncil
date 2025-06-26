import { StateGraph, StateGraphArgs } from "@langchain/langgraph";
import { BaseMessage } from "@langchain/core/messages";
import { TavilySearchResults } from "@langchain/community/tools/tavily_search";

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

// Initialize tools
const tavily = new TavilySearchResults({
  maxResults: 20,
});

// Node 1: Search recent tweets
export async function searchRecentTweets(state: PersonalityState) {
  const oneYearAgo = new Date();
  oneYearAgo.setFullYear(oneYearAgo.getFullYear() - 1);
  const dateString = oneYearAgo.toISOString().split('T')[0];
  
  const query = `${state.personName} tweets after:${dateString}`;
  const results = await tavily.invoke(query);
  
  return {
    tweets: results,
    searchAttempts: state.searchAttempts + 1,
  };
}

// Node 2: Evaluate data sufficiency
export async function evaluateData(state: PersonalityState) {
  const tweets = state.tweets || [];
  const otherContent = state.otherContent || [];
  
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
  
  const results = await tavily.invoke(query);
  
  return {
    otherContent: [...(state.otherContent || []), ...results],
    searchAttempts: state.searchAttempts + 1,
  };
}

// Node 4: Generate response
async function generateResponse(state: PersonalityState) {
  // Here you would implement your LLM generation logic
  // using the collected tweets and content
  
  const allContent = [...state.tweets, ...state.otherContent];
  
  // Example: Use OpenAI or another LLM
  // const response = await generateWithPersonality(state.personName, allContent);
  
  return {
    response: `Generated response based on ${allContent.length} pieces of content`,
  };
}


// Define conditional routing
function shouldSearchMore(state: PersonalityState): string {
  if (state.dataSufficient) {
    return "generate";
  } else if (state.searchAttempts < 4) {
    return "searchMore";
  } else {
    return "generate";
  }
}
