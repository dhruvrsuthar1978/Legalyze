import { useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { Upload, FileText, X, CheckCircle, AlertCircle } from 'lucide-react';
import { uploadStart, uploadSuccess, uploadFailure } from '../store/contractsSlice';
import { showToast } from '../store/uiSlice';
import { contractService } from '../services/contractService';
import { analysisService } from '../services/analysisService';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';

function UploadPage() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (selectedFile) => {
    const maxSize = 10 * 1024 * 1024; // 10MB
    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];

    if (!allowedTypes.includes(selectedFile.type)) {
      dispatch(showToast({
        type: 'error',
        title: 'Invalid File Type',
        message: 'Please upload a PDF or DOCX file',
      }));
      return;
    }

    if (selectedFile.size > maxSize) {
      dispatch(showToast({
        type: 'error',
        title: 'File Too Large',
        message: 'Maximum file size is 10MB',
      }));
      return;
    }

    setFile(selectedFile);
    setUploadStatus(null);
  };

  const removeFile = () => {
    setFile(null);
    setUploadStatus(null);
    setUploadProgress(0);
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setUploadStatus('uploading');
    dispatch(uploadStart());

    try {
      // Choose chunked upload for larger files
      const CHUNK_SIZE = 5 * 1024 * 1024; // 5MB
      const contractTitle = file.name.replace(/\.[^/.]+$/, "");
      let result = null;
      const sessionKey = `upload_session_${file.name}_${file.size}`;

      if (file.size <= CHUNK_SIZE) {
        // Small file - single upload
        const resp = await contractService.uploadContract(file, contractTitle, 'Uploaded via web interface');
        result = resp;
        setUploadProgress(50);
      } else {
        // Chunked upload flow with resume
        let uploadId = localStorage.getItem(sessionKey);

        if (!uploadId) {
          const init = await contractService.initiateChunkedUpload(file.name, file.size);
          uploadId = init.upload_id;
          localStorage.setItem(sessionKey, uploadId);
        }

        const status = await contractService.getUploadStatus(uploadId);
        const uploadedParts = (status && status.parts) || [];

        const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
        let uploadedBytes = uploadedParts.reduce((acc, idx) => {
          const start = idx * CHUNK_SIZE;
          const end = Math.min(start + CHUNK_SIZE, file.size);
          return acc + (end - start);
        }, 0);

        for (let i = 0; i < totalChunks; i++) {
          if (uploadedParts.includes(i)) continue; // skip already uploaded
          const start = i * CHUNK_SIZE;
          const end = Math.min(start + CHUNK_SIZE, file.size);
          const chunk = file.slice(start, end);
          // Upload chunk (with retries handled in service)
          await contractService.uploadChunk(uploadId, i, chunk);
          uploadedBytes += (end - start);
          setUploadProgress(Math.round((uploadedBytes / file.size) * 50));
        }

        // Complete upload
        result = await contractService.completeChunkedUpload(uploadId, file.name, contractTitle, []);
        setUploadProgress(60);
        localStorage.removeItem(sessionKey);
      }

      // finalize UI
      setUploading(false);
      setUploadStatus('uploading');
      dispatch(uploadSuccess(result));
      dispatch(showToast({ type: 'success', title: 'Upload Started', message: 'File uploaded, analysis will begin shortly.' }));

      // Trigger analysis pipeline in background
      try {
        await analysisService.runAnalysis(result.id, 'async');
      } catch (analysisStartError) {
        // Ignore conflict when analysis already exists, fail for other errors
        if (analysisStartError?.response?.status !== 409) {
          throw analysisStartError;
        }
      }

      // Start polling processing status
      let finished = false;
      let attempts = 0;
      const maxAttempts = 120; // 4 minutes at 2s interval

      setUploadStatus('processing');
      setUploadProgress(5);

      const pollInterval = setInterval(async () => {
        attempts += 1;
        try {
          const statusRes = await contractService.getProcessingStatus(result.id);
          const status = statusRes.status || statusRes.analysis_status || statusRes.state || 'processing';
          const progress = statusRes.progress ?? statusRes.percent ?? null;

          if (progress !== null && !isNaN(progress)) {
            setUploadProgress(Math.min(95, Math.max(5, Math.round(progress))));
          } else {
            // animate progress slowly if no exact progress provided
            setUploadProgress(prev => Math.min(95, prev + 5));
          }

          if (status === 'completed' || status === 'done' || status === 'finished') {
            finished = true;
            clearInterval(pollInterval);
            setUploadProgress(100);
            setUploadStatus('success');
            dispatch(uploadSuccess(result));
            dispatch(showToast({ type: 'success', title: 'Analysis Complete', message: 'Contract analysis finished.' }));
            navigate(`/contract/${result.id}`);
          } else if (status === 'failed' || status === 'error') {
            finished = true;
            clearInterval(pollInterval);
            setUploadStatus('error');
            setUploadProgress(0);
            dispatch(uploadFailure('Analysis failed'));
            dispatch(showToast({ type: 'error', title: 'Analysis Failed', message: statusRes.message || 'Analysis failed on server.' }));
          } else if (attempts >= maxAttempts) {
            finished = true;
            clearInterval(pollInterval);
            setUploadStatus('processing');
            dispatch(showToast({ type: 'info', title: 'Processing Delayed', message: 'Analysis is taking longer than expected. You can check status on the contract page.' }));
            navigate(`/contract/${result.id}`);
          }

        } catch (pollErr) {
          // transient network error — keep polling until max attempts
          console.warn('Polling error', pollErr);
        }
      }, 2000);

    } catch (error) {
      setUploading(false);
      setUploadStatus('error');
      
      dispatch(uploadFailure(error.message));
      dispatch(showToast({
        type: 'error',
        title: 'Upload Failed',
        message: error.response?.data?.detail || 'Please try again',
      }));
    }
  };
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold" style={{ color: 'var(--color-text-primary)' }}>Upload Contract 📄</h1>
        <p className="mt-1" style={{ color: 'var(--color-text-tertiary)' }}>Upload your PDF or DOCX contract for AI-powered analysis</p>
      </div>

      <Card>
        {!file ? (
          <div
            className={`border-2 border-dashed rounded-lg p-12 text-center transition-all ${
              dragActive ? 'border-(--color-primary-500) bg-(--color-primary-50)' : 'border-neutral-300'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <Upload className="w-16 h-16 mx-auto mb-4" style={{ color: 'var(--color-neutral-400)' }} />
            <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--color-text-primary)' }}>
              Drop your contract here
            </h3>
            <p className="text-sm mb-4" style={{ color: 'var(--color-text-tertiary)' }}>
              or click to browse your files
            </p>
            <input
              type="file"
              id="file-upload"
              className="hidden"
              onChange={handleChange}
              accept=".pdf,.docx"
              aria-label="Upload contract file"
            />
            <label htmlFor="file-upload">
              <Button as="span" className="cursor-pointer">
                Select File
              </Button>
            </label>
            <p className="text-xs mt-4" style={{ color: 'var(--color-text-tertiary)' }}>
              Supported formats: PDF, DOCX (Max size: 10MB)
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="flex items-center justify-between p-4 rounded-lg" style={{ backgroundColor: 'var(--color-bg-tertiary)' }}>
              <div className="flex items-center gap-3">
                <FileText className="w-10 h-10" style={{ color: 'var(--color-primary-600)' }} />
                <div>
                  <p className="font-medium" style={{ color: 'var(--color-text-primary)' }}>{file.name}</p>
                  <p className="text-sm" style={{ color: 'var(--color-text-tertiary)' }}>
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              </div>
              {uploadStatus !== 'uploading' && uploadStatus !== 'success' && (
                <button
                  onClick={removeFile}
                  className="hover:text-red-600 transition-colors"
                  style={{ color: 'var(--color-neutral-400)' }}
                >
                  <X className="w-5 h-5" />
                </button>
              )}
            </div>

            {(uploadStatus === 'uploading' || uploadStatus === 'processing') && (
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium" style={{ color: 'var(--color-text-secondary)' }}>
                    {uploadStatus === 'processing' ? 'Analyzing...' : 'Uploading...'}
                  </span>
                  <span className="text-sm font-medium" style={{ color: 'var(--color-text-secondary)' }}>{uploadProgress}%</span>
                </div>
                <div className="w-full rounded-full h-2" style={{ backgroundColor: 'var(--color-neutral-200)' }}>
                  <div
                    className="h-2 rounded-full transition-all duration-300"
                    style={{ backgroundColor: 'var(--color-primary-600)', width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}

            {uploadStatus === 'success' && (
              <div className="flex items-center gap-2 p-4 rounded-lg" style={{ backgroundColor: 'var(--color-success-light)', border: '1px solid var(--color-success)' }}>
                <CheckCircle className="w-5 h-5" style={{ color: 'var(--color-success)' }} />
                <div className="flex-1">
                  <p className="text-sm font-medium" style={{ color: 'var(--color-success)' }}>Upload Successful!</p>
                  <p className="text-xs" style={{ color: 'var(--color-success)' }}>Redirecting to analysis page...</p>
                </div>
              </div>
            )}

            {uploadStatus === 'error' && (
              <div className="flex items-center gap-2 p-4 rounded-lg" style={{ backgroundColor: 'var(--color-error-light)', border: '1px solid var(--color-error)' }}>
                <AlertCircle className="w-5 h-5" style={{ color: 'var(--color-error)' }} />
                <div className="flex-1">
                  <p className="text-sm font-medium" style={{ color: 'var(--color-error)' }}>Upload Failed</p>
                  <p className="text-xs" style={{ color: 'var(--color-error)' }}>Please try again</p>
                </div>
              </div>
            )}

            {uploadStatus !== 'uploading' && uploadStatus !== 'success' && (
              <div className="flex gap-3">
                <Button onClick={handleUpload} className="flex-1" loading={uploading}>
                  Upload & Analyze
                </Button>
                <Button variant="outline" onClick={removeFile}>
                  Cancel
                </Button>
              </div>
            )}
          </div>
        )}
      </Card>

      <Card>
        <h3 className="text-lg font-semibold mb-3" style={{ color: 'var(--color-text-primary)' }}>What happens next?</h3>
        <div className="space-y-3">
          <div className="flex items-start gap-3">
            <div className="w-6 h-6 rounded-full flex items-center justify-center shrink-0 mt-0.5" style={{ backgroundColor: 'var(--color-primary-100)' }}>
              <span className="text-xs font-bold" style={{ color: 'var(--color-primary-600)' }}>1</span>
            </div>
            <div>
              <p className="font-medium" style={{ color: 'var(--color-text-primary)' }}>AI Analysis</p>
              <p className="text-sm" style={{ color: 'var(--color-text-tertiary)' }}>Our AI will analyze your contract for clauses, risks, and compliance</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-6 h-6 rounded-full flex items-center justify-center shrink-0 mt-0.5" style={{ backgroundColor: 'var(--color-primary-100)' }}>
              <span className="text-xs font-bold" style={{ color: 'var(--color-primary-600)' }}>2</span>
            </div>
            <div>
              <p className="font-medium" style={{ color: 'var(--color-text-primary)' }}>Plain English Explanation</p>
              <p className="text-sm" style={{ color: 'var(--color-text-tertiary)' }}>Get easy-to-understand explanations of complex legal terms</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-6 h-6 rounded-full flex items-center justify-center shrink-0 mt-0.5" style={{ backgroundColor: 'var(--color-primary-100)' }}>
              <span className="text-xs font-bold" style={{ color: 'var(--color-primary-600)' }}>3</span>
            </div>
            <div>
              <p className="font-medium" style={{ color: 'var(--color-text-primary)' }}>AI Suggestions</p>
              <p className="text-sm" style={{ color: 'var(--color-text-tertiary)' }}>Receive recommendations to improve contract terms and reduce risks</p>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}

export default UploadPage;
