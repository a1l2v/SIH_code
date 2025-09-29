import React, { useState } from 'react';
import { Cloud, Bug, TrendingUp, Building2, Mic, ChevronRight, CloudRain, User } from 'lucide-react';

const FarmAssistantInterface = () => {
  const [activeTab, setActiveTab] = useState('Home');

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
        <div className="mb-6">
          <div className="bg-white/20 backdrop-blur-sm rounded-2xl px-6 py-3 shadow-lg">
            <input
              type="text"
              placeholder="Search..."
              className="w-full bg-transparent text-white placeholder-white/70 outline-none text-lg"
            />
          </div>
        </div>

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
            <div className="bg-green-500 rounded-2xl p-4 mb-4">
              <div className="flex items-center gap-3">
                <Mic className="w-8 h-8 text-white" />
                <span className="text-white text-lg font-medium">Ask a Question</span>
              </div>
            </div>
            
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