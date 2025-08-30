// src/Translator.js
import React, { useState } from "react";
import { Upload, Loader2, CheckCircle2, AlertCircle, Image as ImageIcon } from "lucide-react";

const Translator = () => {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  // Handle file selection
  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (selected) {
      setFile(selected);
      setPreview(URL.createObjectURL(selected));
      setResult(null);
      setError("");
    }
  };

  // Submit image to backend
  const handleSubmit = async () => {
    if (!file) {
      setError("Please select an image first");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const formData = new FormData();
      formData.append("image", file);

      console.log("Sending request to backend...");

      const response = await fetch("http://localhost:5000/api/translate", {
        method: "POST",
        body: formData,
        credentials: "include",
      });

      const data = await response.json();
      console.log("Backend response:", data);
      console.log("Original texts:", data.original_texts);
      console.log("Translated texts:", data.translated_texts);
      
      if (!response.ok) throw new Error(data.error || "Translation failed");

      // Verify data structure before setting result
      if (!data.original_texts || !data.translated_texts) {
        throw new Error("Invalid response format from server");
      }

      setResult(data);
    } catch (err) {
      console.error("Translation error:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto p-6 bg-white rounded-xl shadow-lg">
      <h2 className="text-2xl font-semibold text-gray-800 mb-4 flex items-center gap-2">
        <ImageIcon className="w-6 h-6 text-indigo-600" />
        Signboard Translator
      </h2>

      {/* File Upload */}
      <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
        {preview ? (
          <img
            src={preview}
            alt="Preview"
            className="mx-auto max-h-64 object-contain rounded-lg"
          />
        ) : (
          <p className="text-gray-500">Drag & drop an image or click below</p>
        )}

        <input
          type="file"
          accept="image/*"
          onChange={handleFileChange}
          className="hidden"
          id="file-upload"
        />
        <label
          htmlFor="file-upload"
          className="inline-flex items-center gap-2 mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg cursor-pointer hover:bg-indigo-700 transition-colors"
        >
          <Upload className="w-5 h-5" /> Choose Image
        </label>
      </div>

      {/* Submit Button */}
      <div className="mt-6">
        <button
          onClick={handleSubmit}
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Translating...
            </>
          ) : (
            <>
              <CheckCircle2 className="w-5 h-5" />
              Translate Image
            </>
          )}
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-4 flex items-center gap-2 text-red-600 bg-red-50 border border-red-200 rounded-lg p-3">
          <AlertCircle className="w-5 h-5" />
          {error}
        </div>
      )}

      {/* Debug Info */}
      {result && (
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-xs text-blue-600">Debug Info:</p>
          <p className="text-xs text-blue-700">Original texts count: {result.original_texts?.length || 0}</p>
          <p className="text-xs text-blue-700">Translated texts count: {result.translated_texts?.length || 0}</p>
          <p className="text-xs text-blue-700">Processing time: {result.processing_time}s</p>
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="mt-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-3">
            Translation Result
          </h3>

          {/* Show message if no text detected */}
          {(!result.original_texts || result.original_texts.length === 0) && (
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-yellow-700">No text was detected in the image. Try with a clearer image containing text.</p>
            </div>
          )}

          {/* Processed Image */}
          {result.processed_image && (
            <div className="mb-4">
              <h4 className="text-sm font-medium text-gray-600 mb-2">Processed Image:</h4>
              <img
                src={`data:image/png;base64,${result.processed_image}`}
                alt="Translated"
                className="mx-auto max-h-80 object-contain rounded-lg border"
              />
            </div>
          )}

          {/* Text Translations */}
          {result.original_texts && result.original_texts.length > 0 && (
            <div className="mt-4 space-y-3">
              <h4 className="text-sm font-medium text-gray-600">Detected and Translated Text:</h4>
              {result.original_texts.map((text, i) => {
                console.log(`Rendering item ${i}: Original="${text}", Translated="${result.translated_texts[i]}"`);
                return (
                  <div
                    key={i}
                    className="p-3 border border-gray-200 rounded-lg bg-gray-50"
                  >
                    <div className="mb-2">
                      <p className="text-sm text-gray-600">Original Text:</p>
                      <p className="font-medium text-gray-800 bg-white p-2 rounded border">
                        {text || "No text detected"}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Translation:</p>
                      <p className="font-medium text-green-700 bg-green-50 p-2 rounded border border-green-200">
                        {result.translated_texts && result.translated_texts[i] 
                          ? result.translated_texts[i] 
                          : "Translation not available"}
                      </p>
                    </div>
                    {/* Show if translation is same as original */}
                    {text === result.translated_texts[i] && (
                      <p className="text-xs text-orange-600 mt-1">
                        ℹ️ Translation is same as original (already in target language)
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* Raw JSON Response (for debugging) */}
          <div className="mt-6 p-3 bg-gray-50 border rounded-lg">
            <details>
              <summary className="text-sm font-medium text-gray-600 cursor-pointer">
                Show Raw Response (Debug)
              </summary>
              <pre className="mt-2 text-xs text-gray-700 overflow-auto">
                {JSON.stringify(result, null, 2)}
              </pre>
            </details>
          </div>
        </div>
      )}
    </div>
  );
};

export default Translator;