import React, { useState, useRef } from 'react';
import { Cloud, Bug, TrendingUp, Building2, Mic, ChevronRight, CloudRain, User, Square, Upload, Play, Pause } from 'lucide-react';

const FarmAssistantInterface = () => {
  const [activeTab, setActiveTab] = useState('Home');
  const [isRecording, setIsRecording] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [error, setError] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [responseAudio, setResponseAudio] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const streamRef = useRef(null);
  const audioPlayerRef = useRef(null);

  const startRecording = async () => {
    try {
      setError(null);
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm'
      });
      
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorder.onstop = () => {
        uploadRecording();
      };
      
      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      setError('Failed to access microphone. Please check permissions.');
      console.error('Error accessing microphone:', err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      // Stop all tracks to release microphone
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    }
  };

  const uploadRecording = async () => {
    if (audioChunksRef.current.length === 0) return;
    
    setIsUploading(true);
    setUploadStatus(null);
    
    try {
      const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
      const formData = new FormData();
      
      // Create a filename with timestamp
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const filename = `recording-${timestamp}.mp3`;
      
      formData.append('file', audioBlob, filename);
      
      const response = await fetch('http://localhost:5000/upload-audio', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }
      
      const data = await response.json();
      setUploadStatus({
        success: true,
        filename: data.filename,
        url: data.url,
        message: data.message
      });

      // Now call url_to_response with the uploaded file URL
      await processAudioResponse(data.url);
      
    } catch (err) {
      setError(err.message || 'Failed to upload recording');
      setUploadStatus({ success: false });
    } finally {
      setIsUploading(false);
    }
  };

  const processAudioResponse = async (audioUrl) => {
    setIsProcessing(true);
    
    try {
      const response = await fetch('http://localhost:5000/api/url_to_response', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: audioUrl }),
      });

      if (!response.ok) {
        throw new Error(`Processing failed: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (data.audio_url) {
        setResponseAudio(data.audio_url);
        // Auto-play the response
        setTimeout(() => {
          if (audioPlayerRef.current) {
            audioPlayerRef.current.play();
          }
        }, 100);
      }

    } catch (err) {
      setError(err.message || 'Failed to process audio response');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleRecordingClick = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const handleAudioPlay = () => {
    setIsPlaying(true);
  };

  const handleAudioPause = () => {
    setIsPlaying(false);
  };

  const handleAudioEnded = () => {
    setIsPlaying(false);
    setResponseAudio(null);
    setUploadStatus(null);
  };

  const togglePlayPause = () => {
    if (audioPlayerRef.current) {
      if (isPlaying) {
        audioPlayerRef.current.pause();
      } else {
        audioPlayerRef.current.play();
      }
    }
  };

  const resetStatus = () => {
    setUploadStatus(null);
    setError(null);
    setResponseAudio(null);
    setIsPlaying(false);
  };

  const tabs = [
    { name: 'Home', icon: Building2 },
    { name: 'Assistant', icon: User },
    { name: 'Advisories', icon: Bug },
    { name: 'Activity', icon: TrendingUp }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-300 to-blue-400 flex items-center justify-center p-4">
      {/* Mobile Interface Container */}
      <div className="w-full max-w-sm mx-auto">
        {/* Search Bar */}
        {/* <div className="mb-6">
          <div className="bg-white/20 backdrop-blur-sm rounded-2xl px-6 py-3 shadow-lg">
            <input
              type="text"
              placeholder="Search..."
              className="w-full bg-transparent text-white placeholder-white/70 outline-none text-lg"
            />
          </div>
        </div> */}

        {/* Main Interface */}
        <div className="bg-black/90 rounded-3xl overflow-hidden shadow-2xl">
          {/* Header */}
          <div className="p-6 pb-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-green-500 rounded-lg flex items-center justify-center">
                  <Bug className="w-5 h-5 text-white" />
                </div>
                <span className="text-white font-semibold">Krishi Sakhi</span>
              </div>
              <User className="w-6 h-6 text-white/70" />
            </div>
            
            <h1 className="text-white text-2xl font-bold mb-1">Hello, Rajesh 👋</h1>
            <p className="text-white/70 text-sm">Welcome back to your farm assistant.</p>
          </div>

          {/* Quick Access */}
          <div className="px-6 mb-6">
            <h3 className="text-white font-semibold mb-4">Quick Access</h3>
            
            {/* Recording/Audio Player Button */}
            {responseAudio ? (
              // Audio Player Mode
              <div className="w-full bg-blue-600 rounded-2xl p-4 mb-4">
                <div className="flex items-center gap-3 justify-center mb-3">
                  <button
                    onClick={togglePlayPause}
                    className="bg-white/20 hover:bg-white/30 rounded-full p-3 transition-colors"
                  >
                    {isPlaying ? (
                      <Pause className="w-6 h-6 text-white" />
                    ) : (
                      <Play className="w-6 h-6 text-white" />
                    )}
                  </button>
                  <span className="text-white text-lg font-medium">
                    {isPlaying ? 'Playing Response' : 'Response Ready'}
                  </span>
                </div>
                
                <audio
                  ref={audioPlayerRef}
                  src={responseAudio}
                  onPlay={handleAudioPlay}
                  onPause={handleAudioPause}
                  onEnded={handleAudioEnded}
                  className="hidden"
                />
                
                <button
                  onClick={resetStatus}
                  className="w-full bg-white/20 hover:bg-white/30 text-white rounded-lg py-2 px-4 text-sm transition-colors"
                >
                  Ask Another Question
                </button>
              </div>
            ) : (
              // Recording Button Mode
              <button
                onClick={handleRecordingClick}
                disabled={isUploading || isProcessing}
                className={`w-full rounded-2xl p-4 mb-4 transition-all duration-200 ${
                  isRecording 
                    ? 'bg-red-500 hover:bg-red-600 animate-pulse' 
                    : (isUploading || isProcessing)
                    ? 'bg-gray-500 cursor-not-allowed'
                    : 'bg-green-500 hover:bg-green-600'
                }`}
              >
                <div className="flex items-center gap-3 justify-center">
                  {isProcessing ? (
                    <>
                      <Upload className="w-8 h-8 text-white animate-spin" />
                      <span className="text-white text-lg font-medium">Processing...</span>
                    </>
                  ) : isUploading ? (
                    <>
                      <Upload className="w-8 h-8 text-white animate-spin" />
                      <span className="text-white text-lg font-medium">Uploading...</span>
                    </>
                  ) : isRecording ? (
                    <>
                      <Square className="w-8 h-8 text-white" />
                      <span className="text-white text-lg font-medium">Stop Recording</span>
                    </>
                  ) : (
                    <>
                      <Mic className="w-8 h-8 text-white" />
                      <span className="text-white text-lg font-medium">Ask a Question</span>
                    </>
                  )}
                </div>
              </button>
            )}

            {/* Status Messages */}
            {error && (
              <div className="mb-4 bg-red-500/20 border border-red-500/50 rounded-xl p-3">
                <p className="text-red-200 text-sm text-center">{error}</p>
                <button 
                  onClick={resetStatus}
                  className="mt-2 text-red-300 text-xs underline block mx-auto"
                >
                  Dismiss
                </button>
              </div>
            )}

            {uploadStatus && uploadStatus.success && !responseAudio && (
              <div className="mb-4 bg-green-500/20 border border-green-500/50 rounded-xl p-3">
                <p className="text-green-200 text-sm text-center font-medium">
                  {isProcessing ? 'Getting response...' : uploadStatus.message}
                </p>
                {!isProcessing && (
                  <p className="text-green-300 text-xs text-center mt-1">
                    File: {uploadStatus.filename}
                  </p>
                )}
              </div>
            )}
            
            <div className="grid grid-cols-4 gap-3">
              <div className="bg-white/10 rounded-xl p-3 text-center">
                <Cloud className="w-6 h-6 text-white mx-auto mb-1" />
                <span className="text-white/80 text-xs">Weather</span>
              </div>
              <div className="bg-white/10 rounded-xl p-3 text-center">
                <Bug className="w-6 h-6 text-green-400 mx-auto mb-1" />
                <span className="text-white/80 text-xs">Pest Alert</span>
              </div>
              <div className="bg-white/10 rounded-xl p-3 text-center">
                <TrendingUp className="w-6 h-6 text-white mx-auto mb-1" />
                <span className="text-white/80 text-xs">Market Prices</span>
              </div>
              <div className="bg-white/10 rounded-xl p-3 text-center">
                <Building2 className="w-6 h-6 text-white mx-auto mb-1" />
                <span className="text-white/80 text-xs">Govt Schemes</span>
              </div>
            </div>
          </div>

          {/* Advisory Highlights */}
          <div className="px-6 mb-6">
            <h3 className="text-white font-semibold mb-4">Advisory Highlights</h3>
            <div className="bg-gradient-to-r from-teal-800 to-teal-600 rounded-2xl p-4 relative overflow-hidden">
              <div className="absolute inset-0 opacity-20">
                <div className="w-full h-full bg-cover bg-center" 
                     style={{backgroundImage: 'url("data:image/svg+xml,%3Csvg width="100" height="100" xmlns="http://www.w3.org/2000/svg"%3E%3Cdefs%3E%3Cpattern id="leaf" patternUnits="userSpaceOnUse" width="20" height="20"%3E%3Cpath d="M10 2C15 7 15 13 10 18C5 13 5 7 10 2Z" fill="white" opacity="0.1"/%3E%3C/pattern%3E%3C/defs%3E%3Crect width="100" height="100" fill="url(%23leaf)"/%3E%3C/svg%3E")'}}></div>
              </div>
              <div className="relative flex items-start gap-3">
                <CloudRain className="w-8 h-8 text-white mt-1" />
                <div className="flex-1">
                  <h4 className="text-white font-semibold mb-1">Rain expected tomorrow, delay spraying pesticide</h4>
                  <p className="text-white/80 text-sm">Updated 2 hours ago</p>
                </div>
              </div>
            </div>
          </div>

          {/* Notifications */}
          <div className="px-6 mb-6">
            <h3 className="text-white font-semibold mb-4">Notifications</h3>
            
            <div className="space-y-3">
              <div className="flex items-center gap-3 p-3 bg-white/5 rounded-xl">
                <div className="w-10 h-10 bg-green-500/20 rounded-xl flex items-center justify-center">
                  <Bug className="w-5 h-5 text-green-400" />
                </div>
                <div className="flex-1">
                  <h4 className="text-white font-medium text-sm">Pest Alert</h4>
                  <p className="text-white/60 text-xs">New advisory on pest control for rice paddies.</p>
                </div>
                <ChevronRight className="w-5 h-5 text-white/40" />
              </div>
              
              <div className="flex items-center gap-3 p-3 bg-white/5 rounded-xl">
                <div className="w-10 h-10 bg-blue-500/20 rounded-xl flex items-center justify-center">
                  <Cloud className="w-5 h-5 text-blue-400" />
                </div>
                <div className="flex-1">
                  <h4 className="text-white font-medium text-sm">Weather Update</h4>
                  <p className="text-white/60 text-xs">Reminder: Check today's weather forecast</p>
                </div>
                <ChevronRight className="w-5 h-5 text-white/40" />
              </div>
            </div>
          </div>

          {/* Bottom Navigation */}
          <div className="bg-black/50 px-6 py-4 border-t border-white/10">
            <div className="flex justify-between">
              {tabs.map((tab) => (
                <button
                  key={tab.name}
                  onClick={() => setActiveTab(tab.name)}
                  className={`flex flex-col items-center gap-1 px-3 py-2 rounded-lg transition-colors ${
                    activeTab === tab.name 
                      ? 'text-green-400' 
                      : 'text-white/60 hover:text-white'
                  }`}
                >
                  <tab.icon className="w-5 h-5" />
                  <span className="text-xs font-medium">{tab.name}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FarmAssistantInterface;