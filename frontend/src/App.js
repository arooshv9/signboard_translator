// src/App.js
import React, { useState } from "react";
import Translator from "./Translator";
import TranslationHistory from "./TranslationHistory";

const App = () => {
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);

  return (
    <div className="min-h-screen bg-blue-50 flex flex-col items-center justify-center p-6">
      <Translator />

      <button
        onClick={() => setIsHistoryOpen(true)}
        className="mt-6 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
      >
        View Translation History
      </button>

      <TranslationHistory
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
      />
    </div>
  );
};

export default App;
