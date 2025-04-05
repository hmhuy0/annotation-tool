import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { CSS_COLOR_NAMES } from "../assets/color_assets";

import { base_url } from "../assets/base_url";
// Don't reuse the same controller for all requests - this is causing problems
// let controller = new AbortController();



export const explainPattern = createAsyncThunk(
    "workspace/explainpattern",
    async (request, { getState }) => {
      const state = getState();
      const { pattern } = request;
  
      var url = new URL(`${base_url}/explain/${pattern}`);
  
      const data = await fetch(url, {
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
          credentials: "include",
          annotuser: window.localStorage.getItem("user").replaceAll('"', ""),
        },
        method: "GET",
      }).then((response) => response.json());
  
      return data;
    }
  );
  
  export const deletePattern = createAsyncThunk(
    "workspace/deletePattern",
    async (request, { getState }) => {
      const { theme, pattern } = request;
      var url = new URL(`${base_url}/delete_pattern`);
  
      const data = await fetch(url, {
        headers: {
          "Content-Type": "application/json",
          credentials: "include",
          annotuser: window.localStorage.getItem("user").replaceAll('"', ""),
        },
        method: "POST",
        body: JSON.stringify({ theme: theme, pattern: pattern }),
      }).then((response) => response.json());
  
      return data;
    }
  );
  
  export const pinPattern = createAsyncThunk(
    "workspace/pinPattern",
    async (request, { getState }) => {
      const { theme, pattern } = request;
      var url = new URL(`${base_url}/pin_pattern`);
  
      const data = await fetch(url, {
        headers: {
          "Content-Type": "application/json",
          credentials: "include",
          annotuser: window.localStorage.getItem("user").replaceAll('"', ""),
        },
        method: "POST",
        body: JSON.stringify({ theme: theme, pattern: pattern }),
      }).then((response) => response.json());
  
      return data;
    }
  );


export const fetchRelatedExample = createAsyncThunk(
    "workspace/related_examples",
    async (request, { getState }) => {
      const state = getState();
  
      const { id } = request;
  
      var url = new URL(`${base_url}/related_examples/${id}`);
  
      const data = await fetch(url, {
        headers: {
          "Content-Type": "application/json",
          credentials: "include",
          annotuser: window.localStorage.getItem("user").replaceAll('"', ""),
        },
        method: "GET",
      }).then((response) => response.json());
  
      return data;
    }
  );

  export const fetchPatterns = createAsyncThunk(
    "workspace/patterns",
    async (request, { getState }) => {
      // Create a new controller for each request
      const controller = new AbortController();
      console.log(`[fetchPatterns] Created new controller for this request`);
      
      const signal = controller.signal;
      console.log(`[fetchPatterns] Signal aborted: ${signal.aborted}`);
  
      var url = new URL(`${base_url}/patterns`);
      console.log(`[fetchPatterns] Requesting URL: ${url.toString()}`);
  
      try {
        const userStr = window.localStorage.getItem("user");
        const user = userStr ? userStr.replaceAll('"', "") : "unknown";
        console.log(`[fetchPatterns] Making fetch request as user: ${user}`);
        
        console.time(`[fetchPatterns] Request time`);
        const response = await fetch(url, {
          signal: signal,
          headers: {
            "Content-Type": "application/json",
            credentials: "include",
            annotuser: user,
          },
          method: "GET",
        });
        console.timeEnd(`[fetchPatterns] Request time`);
        
        console.log(`[fetchPatterns] Response status: ${response.status}`);
        
        if (!response.ok) {
          throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        }
        
        console.time(`[fetchPatterns] JSON parse time`);
        const data = await response.json();
        console.timeEnd(`[fetchPatterns] JSON parse time`);
        
        console.log(`[fetchPatterns] Parsed JSON response:`, data);
  
        return data;
      } catch (error) {
        console.error(`[fetchPatterns] ERROR:`, error);
        console.error(`[fetchPatterns] Error message: ${error.message}`);
        console.error(`[fetchPatterns] Error name: ${error.name}`);
        throw error;
      }
    }
  );

  export const fetchCombinedPatterns = createAsyncThunk(
    "workspace/combinedpatterns",
    async (request, { getState }) => {
      // Create a new controller for each request
      const controller = new AbortController();
      console.log(`[fetchCombinedPatterns] Created new controller for this request`);
      
      const signal = controller.signal;
      console.log(`[fetchCombinedPatterns] Signal aborted: ${signal.aborted}`);
      
      const state = getState();
      const { currentBatch, batchSize } = request || {};

      console.log(`[fetchCombinedPatterns] START - Batch: ${currentBatch}, Size: ${batchSize}`);
      
      // Safely access nested properties
      let selectedTheme = "null";
      if (state && state.workspace && state.workspace.selectedTheme) {
        selectedTheme = state.workspace.selectedTheme;
      }
      console.log(`[fetchCombinedPatterns] Current state: ${selectedTheme}`);

      try {
        const userStr = window.localStorage.getItem("user");
        const user = userStr ? userStr.replaceAll('"', "") : "unknown";
        console.log(`[fetchCombinedPatterns] User from localStorage: ${user}`);
        
        // Call the direct BERT endpoint to get GPT predictions
        // This bypasses pattern recognition completely
        const url = new URL(`${base_url}/api/${user}/BERT`);
        if (currentBatch !== undefined && batchSize !== undefined) {
          url.searchParams.append('batch', currentBatch);
          url.searchParams.append('batch_size', batchSize);
        }
        
        console.log(`[fetchCombinedPatterns] Using BERT endpoint URL: ${url.toString()}`);
        console.log(`[fetchCombinedPatterns] Headers: Content-Type=application/json, credentials=include, annotuser=${user}`);
        
        console.time(`[fetchCombinedPatterns] Request time - Batch ${currentBatch}`);
        
        const response = await fetch(url, {
          signal: signal,
          headers: {
            "Content-Type": "application/json",
            credentials: "include",
            authorization: `Bearer ${user}`,
            annotuser: user,
          },
          method: "GET",
        });
        
        console.timeEnd(`[fetchCombinedPatterns] Request time - Batch ${currentBatch}`);
        console.log(`[fetchCombinedPatterns] Received response status: ${response.status}`);
        
        if (!response.ok) {
          throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        }
        
        console.time(`[fetchCombinedPatterns] JSON parse time - Batch ${currentBatch}`);
        const data = await response.json();
        console.timeEnd(`[fetchCombinedPatterns] JSON parse time - Batch ${currentBatch}`);
        
        console.log(`[fetchCombinedPatterns] Parsed JSON response:`, data);
        console.log(`[fetchCombinedPatterns] END - Batch: ${currentBatch}, Size: ${batchSize}`);
        
        return data;
      } catch (error) {
        console.error(`[fetchCombinedPatterns] ERROR for batch ${currentBatch}:`, error);
        console.error(`[fetchCombinedPatterns] Error message: ${error.message}`);
        console.error(`[fetchCombinedPatterns] Error name: ${error.name}`);
        console.error(`[fetchCombinedPatterns] Error stack: ${error.stack}`);
        throw error;
      }
    }
  );

  export const deleteSoftmatch = createAsyncThunk(
    "workspace/delete_softmatch_globally",
    async (request, { getState }) => {
      const { pivot_word, similar_word } = request;
  
      var url = new URL(
        `${base_url}/delete_softmatch_globally/${pivot_word}/${similar_word}`
      );
  
      const data = await fetch(url, {
        headers: {
          "Content-Type": "application/json",
          credentials: "include",
          annotuser: window.localStorage.getItem("user").replaceAll('"', ""),
        },
        method: "GET",
      }).then((response) => response.json());
  
      return data;
    }
  );

  export const setGPTConfig = createAsyncThunk(
    "workspace/setGPTConfig",
    async (request, { getState }) => {
      // Create a new controller for each request
      const controller = new AbortController();
      console.log(`[setGPTConfig] Created new controller for this request`);
      
      const signal = controller.signal;
      console.log(`[setGPTConfig] Signal aborted: ${signal.aborted}`);
      
      const { model, use_gpt } = request;
      console.log(`[setGPTConfig] Setting config: model=${model}, use_gpt=${use_gpt}`);

      var url = new URL(`${base_url}/gpt_config`);
      console.log(`[setGPTConfig] Requesting URL: ${url.toString()}`);

      try {
        const userStr = window.localStorage.getItem("user");
        const user = userStr ? userStr.replaceAll('"', "") : "unknown";
        console.log(`[setGPTConfig] Making fetch request as user: ${user}`);
        
        console.time(`[setGPTConfig] Request time`);
        const response = await fetch(url, {
          signal: signal,
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            credentials: "include",
            annotuser: user,
          },
          body: JSON.stringify({
            model: model,
            use_gpt: use_gpt
          }),
        });
        console.timeEnd(`[setGPTConfig] Request time`);
        
        console.log(`[setGPTConfig] Response status: ${response.status}`);
        
        if (!response.ok) {
          throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        }
        
        console.time(`[setGPTConfig] JSON parse time`);
        const data = await response.json();
        console.timeEnd(`[setGPTConfig] JSON parse time`);
        
        console.log(`[setGPTConfig] Parsed JSON response:`, data);

        return data;
      } catch (error) {
        console.error(`[setGPTConfig] ERROR:`, error);
        console.error(`[setGPTConfig] Error message: ${error.message}`);
        console.error(`[setGPTConfig] Error name: ${error.name}`);
        throw error;
      }
    }
  );
  