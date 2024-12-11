import { useState } from "react";
import "./App.css";

function App() {
  const [documentFile, setDocumentFile] = useState<any>(null);
  const [templateFile, setTemplateFile] = useState<any>(null);
  const [isProcessing, setIsProcessing] = useState<any>(false);
  const [error, setError] = useState("");

  // Handle document file selection
  const handleDocumentFileChange = (event: any) => {
    const file = event.target.files[0];

    // Validate file type
    const allowedTypes = ["application/pdf", "image/jpeg", "image/png"];
    if (!allowedTypes.includes(file.type)) {
      setError("Invalid document type. Please upload PDF or image.");
      return;
    }

    // Validate file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      setError("File is too large. Maximum size is 10MB.");
      return;
    }

    setDocumentFile(file);
    setError("");
  };

  // Handle template file selection
  const handleTemplateFileChange = (event: any) => {
    const file = event.target.files[0];

    // Validate Excel file types
    const allowedTypes = [
      "application/vnd.ms-excel",
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ];

    if (!allowedTypes.includes(file.type)) {
      setError("Invalid template. Please upload an Excel file.");
      return;
    }

    setTemplateFile(file);
    setError("");
  };

  // Submit handler
  const handleSubmit = async (event: any) => {
    event.preventDefault();

    // Validate inputs
    if (!documentFile) {
      setError("Please upload a document");
      return;
    }

    if (!templateFile) {
      setError("Please upload an Excel template");
      return;
    }

    // Create form data
    const formData = new FormData();
    formData.append("document", documentFile);
    formData.append("template", templateFile);

    try {
      setIsProcessing(true);
      setError("");

      // Send to backend
      const response = await fetch(
        "http://127.0.0.1:5000/api/process-document",
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) {
        throw new Error("Document processing failed");
      }

      // Handle successful response
      const result = await response.json();

      // Optionally trigger file download or show success message
      if (result.downloadUrl) {
        window.open(result.downloadUrl, "_blank");
      }
    } catch (err: any) {
      setError(err.message || "An error occurred during processing");
    } finally {
      setIsProcessing(false);
    }
  };

  // Reset form
  const handleReset = () => {
    setDocumentFile(null);
    setTemplateFile(null);
    setError("");

    // Reset file input elements
    if (document.getElementById("document-upload")) {
      // @ts-ignore
      document.getElementById("document-upload").value = "";
    }
    if (document.getElementById("template-upload")) {
      // @ts-ignore
      document.getElementById("template-upload").value = "";
    }
  };

  return (
    <div className="max-w-md mx-auto p-6 bg-white rounded-lg shadow-md">
      <form onSubmit={handleSubmit} className="space-y-4">
        <h2 className="text-2xl font-bold text-center mb-4">
          Document Processing
        </h2>

        {/* Document File Upload */}
        <div>
          <label
            htmlFor="document-upload"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            Upload Document (PDF/Image)
          </label>
          <input
            type="file"
            id="document-upload"
            accept=".pdf,.jpg,.jpeg,.png"
            onChange={handleDocumentFileChange}
            className="w-full p-2 border rounded-md"
          />
          {documentFile && (
            <p className="text-sm text-gray-600 mt-1">
              Selected: {documentFile.name}
            </p>
          )}
        </div>

        {/* Template File Upload */}
        <div>
          <label
            htmlFor="template-upload"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            Upload Excel Template
          </label>
          <input
            type="file"
            id="template-upload"
            accept=".xls,.xlsx"
            onChange={handleTemplateFileChange}
            className="w-full p-2 border rounded-md"
          />
          {templateFile && (
            <p className="text-sm text-gray-600 mt-1">
              Selected: {templateFile.name}
            </p>
          )}
        </div>

        {/* Error Display */}
        {error && (
          <div
            className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative"
            role="alert"
          >
            <span className="block sm:inline">{error}</span>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex space-x-4">
          <button
            type="submit"
            disabled={isProcessing}
            className="flex-1 bg-blue-500 text-white py-2 rounded-md hover:bg-blue-600 disabled:bg-blue-300"
          >
            {isProcessing ? "Processing..." : "Process Document"}
          </button>
          <button
            type="button"
            onClick={handleReset}
            className="flex-1 bg-gray-200 text-gray-700 py-2 rounded-md hover:bg-gray-300"
          >
            Reset
          </button>
        </div>
      </form>
    </div>
  );
}

export default App;
