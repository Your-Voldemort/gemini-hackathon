# LegalMind: Frontend Changes Guide

This document details all frontend changes required to transform the legacy procurement system into LegalMind.

---

## Table of Contents

1. [Overview](#overview)
2. [Updated Pages](#updated-pages)
3. [New Pages](#new-pages)
4. [New Components](#new-components)
5. [API Routes](#api-routes)
6. [Styling Updates](#styling-updates)

---

## 1. Overview

### Current Structure
```
frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   ├── globals.css
│   ├── chat/              # Main chat interface
│   ├── dashboard/         # Risk heatmap (geography-based)
│   ├── reports/           # Generated reports list
│   ├── thinking-logs/     # Agent reasoning viewer
│   └── api/               # Next.js API routes
├── components/
│   ├── app-sidebar.tsx
│   └── ui/                # shadcn components
└── lib/
    └── utils.ts
```

### Target Structure
```
frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   ├── globals.css
│   ├── chat/              # Legal chat with PDF upload
│   ├── contracts/         # NEW: Contract management
│   │   ├── page.tsx       # Contract list
│   │   ├── [id]/          # Contract detail
│   │   └── upload/        # Upload page
│   ├── dashboard/         # Risk/compliance charts
│   ├── documents/         # Renamed from reports
│   ├── thinking-logs/     # Agent reasoning (minor updates)
│   └── api/               # Updated API routes
├── components/
│   ├── app-sidebar.tsx    # Updated navigation
│   ├── contract-upload.tsx
│   ├── contract-card.tsx
│   ├── clause-card.tsx
│   ├── risk-badge.tsx
│   ├── risk-chart.tsx
│   ├── compliance-checklist.tsx
│   └── ui/
└── lib/
    └── utils.ts
```

---

## 2. Updated Pages

### 2.1 Chat Page (`app/chat/page.tsx`)

#### Changes Required:
1. Add PDF upload functionality
2. Display contract context when analyzing
3. Show citations from Google Search
4. Update placeholder text for legal context
5. Add quick action buttons

#### Updated Code:

```tsx
'use client';

import { ChatBubble, ChatBubbleAction, ChatBubbleAvatar, ChatBubbleMessage } from '@/components/ui/chat/chat-bubble';
import { ChatInput } from '@/components/ui/chat/chat-input';
import { ChatMessageList } from '@/components/ui/chat/chat-message-list';
import { Button } from '@/components/ui/button';
import { CopyIcon, CornerDownLeft, RefreshCcw, Volume2, Upload, FileText, Scale, Shield } from 'lucide-react';
import { useEffect, useRef, useState, useCallback } from 'react';
import styles from './markdown-styles-1.module.css';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import CodeDisplayBlock from '@/components/code-display-block';
import { SidebarInset, SidebarProvider, SidebarTrigger } from '@/components/ui/sidebar';
import { ChatSessionSidebar } from './chat-session-sidebar';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card, CardContent } from '@/components/ui/card';
import { useDropzone } from 'react-dropzone';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  convo_id?: string;
  agent_name?: string;
  citations?: Citation[];
}

interface Citation {
  title: string;
  uri: string;
}

interface ContractContext {
  contract_id: string;
  title: string;
  contract_type?: string;
}

export default function ChatPage() {
  const [isGenerating, setIsGenerating] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [contractContext, setContractContext] = useState<ContractContext | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content: `Hello! I'm LegalMind, your AI legal research assistant. I can help you:

• **Analyze contracts** - Upload a PDF and I'll extract key terms, identify risks, and check compliance
• **Research legal questions** - I'll search for relevant case law and regulations with citations
• **Generate reports** - Create professional legal memos and summaries

What would you like to work on today?`,
    },
  ]);
  const [input, setInput] = useState('');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);

  const messagesRef = useRef<HTMLDivElement>(null);
  const formRef = useRef<HTMLFormElement>(null);

  // File upload handler
  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file && file.type === 'application/pdf') {
      setUploadedFile(file);
      
      // Upload the file
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', file.name);
      
      try {
        const response = await fetch('/api/contracts', {
          method: 'POST',
          body: formData,
        });
        
        const data = await response.json();
        
        if (data.contract_id) {
          setContractContext({
            contract_id: data.contract_id,
            title: file.name,
          });
          
          // Add system message about upload
          const uploadMessage: ChatMessage = {
            id: Date.now().toString(),
            role: 'assistant',
            content: `I've received your contract: **${file.name}**

Would you like me to:
1. **Analyze the contract** - Extract key terms, parties, and dates
2. **Assess risks** - Identify potentially problematic clauses
3. **Check compliance** - Verify against GDPR, HIPAA, or other regulations
4. **Generate a summary** - Create an executive summary

Just let me know what you'd like to do!`,
          };
          setMessages(prev => [...prev, uploadMessage]);
        }
      } catch (error) {
        console.error('Upload error:', error);
      }
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1,
    noClick: true,
  });

  useEffect(() => {
    if (messagesRef.current) {
      messagesRef.current.scrollTop = messagesRef.current.scrollHeight;
    }
  }, [messages]);

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (isGenerating || !input) return;
      handleSubmit(e as unknown as React.FormEvent<HTMLFormElement>);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!input.trim() || isGenerating) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsGenerating(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: input.trim(),
          session_id: sessionId,
          contract_id: contractContext?.contract_id,
        }),
      });

      const data = await response.json();

      if (data.status === 'success') {
        if (data.session_id) {
          setSessionId(data.session_id);
        }

        const botMessage: ChatMessage = {
          id: data.session_id || Date.now().toString(),
          role: 'assistant',
          content: data.response,
          agent_name: data.agent_name,
          citations: data.citations,
        };
        setMessages((prev) => [...prev, botMessage]);
      } else {
        const errorMessage: ChatMessage = {
          id: Date.now().toString(),
          role: 'assistant',
          content: `Error: ${data.error || 'Something went wrong'}`,
        };
        setMessages((prev) => [...prev, errorMessage]);
      }
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: 'Sorry, there was an error connecting to the server.',
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleQuickAction = (action: string) => {
    setInput(action);
  };

  const renderCitations = (citations: Citation[]) => {
    if (!citations || citations.length === 0) return null;
    
    return (
      <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        <p className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Sources:</p>
        <div className="space-y-1">
          {citations.map((citation, index) => (
            <a
              key={index}
              href={citation.uri}
              target="_blank"
              rel="noopener noreferrer"
              className="block text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 truncate"
            >
              [{index + 1}] {citation.title || citation.uri}
            </a>
          ))}
        </div>
      </div>
    );
  };

  return (
    <SidebarProvider>
      <ChatSessionSidebar />
      <SidebarInset>
        <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
          <SidebarTrigger className="-ml-1" />
          <div className="flex items-center gap-2">
            <Scale className="h-5 w-5 text-primary" />
            <span className="font-semibold">LegalMind</span>
          </div>
          {contractContext && (
            <Badge variant="secondary" className="ml-4">
              <FileText className="h-3 w-3 mr-1" />
              {contractContext.title}
            </Badge>
          )}
        </header>
        
        <div {...getRootProps()} className="flex flex-1 flex-col relative">
          <input {...getInputProps()} />
          
          {isDragActive && (
            <div className="absolute inset-0 bg-primary/10 border-2 border-dashed border-primary rounded-lg z-50 flex items-center justify-center">
              <div className="text-center">
                <Upload className="h-12 w-12 mx-auto text-primary mb-2" />
                <p className="text-lg font-medium">Drop your contract PDF here</p>
              </div>
            </div>
          )}
          
          <ChatMessageList ref={messagesRef} className="flex-1 p-4">
            {messages.map((message, index) => (
              <ChatBubble
                key={message.id}
                variant={message.role === 'user' ? 'sent' : 'received'}
              >
                <ChatBubbleAvatar
                  src={message.role === 'user' ? '/user-avatar.png' : '/legal-ai-avatar.png'}
                  fallback={message.role === 'user' ? 'US' : 'LM'}
                />
                <ChatBubbleMessage>
                  {message.agent_name && (
                    <Badge variant="outline" className="mb-2 text-xs">
                      {message.agent_name.replace('_AGENT', '').replace(/_/g, ' ')}
                    </Badge>
                  )}
                  <div className={styles.markdown}>
                    <Markdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        code({ node, inline, className, children, ...props }) {
                          const match = /language-(\w+)/.exec(className || '');
                          return !inline && match ? (
                            <CodeDisplayBlock code={String(children).replace(/\n$/, '')} lang={match[1]} />
                          ) : (
                            <code className={className} {...props}>
                              {children}
                            </code>
                          );
                        },
                      }}
                    >
                      {message.content}
                    </Markdown>
                  </div>
                  {message.citations && renderCitations(message.citations)}
                </ChatBubbleMessage>
                {message.role === 'assistant' && (
                  <ChatBubbleAction
                    className="flex gap-1"
                    onClick={() => navigator.clipboard.writeText(message.content)}
                  >
                    <CopyIcon className="h-4 w-4" />
                  </ChatBubbleAction>
                )}
              </ChatBubble>
            ))}
            
            {isGenerating && (
              <ChatBubble variant="received">
                <ChatBubbleAvatar src="/legal-ai-avatar.png" fallback="LM" />
                <ChatBubbleMessage isLoading />
              </ChatBubble>
            )}
          </ChatMessageList>

          {/* Quick Actions */}
          {messages.length <= 2 && (
            <div className="px-4 pb-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleQuickAction('Analyze this contract for risks')}
                >
                  <Shield className="h-4 w-4 mr-2" />
                  Risk Analysis
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleQuickAction('Check compliance with GDPR')}
                >
                  <Scale className="h-4 w-4 mr-2" />
                  GDPR Check
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleQuickAction('Extract all key terms and dates')}
                >
                  <FileText className="h-4 w-4 mr-2" />
                  Extract Terms
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleQuickAction('Generate an executive summary')}
                >
                  <FileText className="h-4 w-4 mr-2" />
                  Summary
                </Button>
              </div>
            </div>
          )}

          <form
            ref={formRef}
            onSubmit={handleSubmit}
            className="sticky bottom-0 border-t bg-background p-4"
          >
            <div className="flex gap-2">
              <Button
                type="button"
                variant="outline"
                size="icon"
                onClick={() => document.querySelector<HTMLInputElement>('input[type="file"]')?.click()}
              >
                <Upload className="h-4 w-4" />
              </Button>
              <ChatInput
                value={input}
                onChange={handleInputChange}
                onKeyDown={onKeyDown}
                placeholder="Ask a legal question or describe what you need..."
                className="flex-1"
              />
              <Button type="submit" disabled={isGenerating || !input.trim()}>
                <CornerDownLeft className="h-4 w-4" />
              </Button>
            </div>
          </form>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
```

---

### 2.2 Dashboard Page (`app/dashboard/page.tsx`)

#### Changes Required:
1. Replace geography map with risk distribution charts
2. Add compliance overview
3. Add contract statistics
4. Update to legal theme

#### Key Components to Add:

```tsx
// Risk Distribution Chart
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

const RISK_COLORS = {
  low: '#22c55e',      // green
  medium: '#f59e0b',   // amber
  high: '#ef4444',     // red
  critical: '#7c2d12', // dark red
};

interface RiskDistribution {
  low: number;
  medium: number;
  high: number;
  critical: number;
}

function RiskDistributionChart({ data }: { data: RiskDistribution }) {
  const chartData = [
    { name: 'Low Risk', value: data.low, color: RISK_COLORS.low },
    { name: 'Medium Risk', value: data.medium, color: RISK_COLORS.medium },
    { name: 'High Risk', value: data.high, color: RISK_COLORS.high },
    { name: 'Critical', value: data.critical, color: RISK_COLORS.critical },
  ].filter(d => d.value > 0);

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={chartData}
          dataKey="value"
          nameKey="name"
          cx="50%"
          cy="50%"
          outerRadius={100}
          label
        >
          {chartData.map((entry, index) => (
            <Cell key={index} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}
```

---

## 3. New Pages

### 3.1 Contracts List Page (`app/contracts/page.tsx`)

```tsx
'use client';

import { useEffect, useState } from 'react';
import { AppSidebar } from '@/components/app-sidebar';
import { SidebarInset, SidebarProvider, SidebarTrigger } from '@/components/ui/sidebar';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Plus, Search, FileText, AlertTriangle, CheckCircle } from 'lucide-react';
import Link from 'next/link';
import { RiskBadge } from '@/components/risk-badge';

interface Contract {
  id: string;
  title: string;
  contract_type: string;
  status: string;
  parties: { name: string; role: string }[];
  overall_risk_score: number;
  compliance_status: string;
  created_at: string;
}

export default function ContractsPage() {
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');

  useEffect(() => {
    fetchContracts();
  }, [statusFilter, typeFilter]);

  const fetchContracts = async () => {
    try {
      const params = new URLSearchParams();
      if (statusFilter !== 'all') params.append('status', statusFilter);
      if (typeFilter !== 'all') params.append('contract_type', typeFilter);
      
      const response = await fetch(`/api/contracts?${params}`);
      const data = await response.json();
      setContracts(data.contracts || []);
    } catch (error) {
      console.error('Error fetching contracts:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredContracts = contracts.filter(contract =>
    contract.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    contract.parties?.some(p => p.name.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
      active: 'default',
      draft: 'secondary',
      expired: 'destructive',
      terminated: 'outline',
    };
    return <Badge variant={variants[status] || 'default'}>{status}</Badge>;
  };

  const getComplianceIcon = (status: string) => {
    if (status === 'compliant') {
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    } else if (status === 'non-compliant') {
      return <AlertTriangle className="h-4 w-4 text-red-500" />;
    }
    return <AlertTriangle className="h-4 w-4 text-amber-500" />;
  };

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
          <SidebarTrigger className="-ml-1" />
          <div className="flex items-center justify-between w-full">
            <h1 className="text-xl font-semibold">Contracts</h1>
            <Link href="/contracts/upload">
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Upload Contract
              </Button>
            </Link>
          </div>
        </header>

        <div className="p-6">
          {/* Filters */}
          <div className="flex gap-4 mb-6">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search contracts..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="draft">Draft</SelectItem>
                <SelectItem value="expired">Expired</SelectItem>
              </SelectContent>
            </Select>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="NDA">NDA</SelectItem>
                <SelectItem value="MSA">MSA</SelectItem>
                <SelectItem value="Employment">Employment</SelectItem>
                <SelectItem value="Lease">Lease</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Contract Grid */}
          {loading ? (
            <div className="text-center py-12">Loading...</div>
          ) : filteredContracts.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium">No contracts found</h3>
              <p className="text-muted-foreground">Upload a contract to get started</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredContracts.map((contract) => (
                <Link href={`/contracts/${contract.id}`} key={contract.id}>
                  <Card className="hover:shadow-lg transition-shadow cursor-pointer">
                    <CardHeader className="pb-2">
                      <div className="flex items-start justify-between">
                        <div>
                          <CardTitle className="text-base">{contract.title}</CardTitle>
                          <CardDescription>{contract.contract_type}</CardDescription>
                        </div>
                        {getStatusBadge(contract.status)}
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Risk Score</span>
                          <RiskBadge score={contract.overall_risk_score} />
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Compliance</span>
                          <div className="flex items-center gap-1">
                            {getComplianceIcon(contract.compliance_status)}
                            <span className="capitalize">{contract.compliance_status}</span>
                          </div>
                        </div>
                        {contract.parties && contract.parties.length > 0 && (
                          <div className="text-sm text-muted-foreground">
                            Parties: {contract.parties.map(p => p.name).join(', ')}
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          )}
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
```

---

### 3.2 Contract Upload Page (`app/contracts/upload/page.tsx`)

```tsx
'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useDropzone } from 'react-dropzone';
import { AppSidebar } from '@/components/app-sidebar';
import { SidebarInset, SidebarProvider, SidebarTrigger } from '@/components/ui/sidebar';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Upload, FileText, X, Loader2 } from 'lucide-react';
import { Progress } from '@/components/ui/progress';

export default function ContractUploadPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const selectedFile = acceptedFiles[0];
    if (selectedFile) {
      setFile(selectedFile);
      setTitle(selectedFile.name.replace('.pdf', ''));
      setError(null);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024, // 50MB
  });

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setProgress(10);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', title || file.name);

      setProgress(30);

      const response = await fetch('/api/contracts', {
        method: 'POST',
        body: formData,
      });

      setProgress(70);

      const data = await response.json();

      if (data.contract_id) {
        setProgress(100);
        // Redirect to chat with contract context
        router.push(`/chat?contract_id=${data.contract_id}`);
      } else {
        throw new Error(data.error || 'Upload failed');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
      setUploading(false);
      setProgress(0);
    }
  };

  const removeFile = () => {
    setFile(null);
    setTitle('');
    setError(null);
  };

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
          <SidebarTrigger className="-ml-1" />
          <h1 className="text-xl font-semibold">Upload Contract</h1>
        </header>

        <div className="p-6 max-w-2xl mx-auto">
          <Card>
            <CardHeader>
              <CardTitle>Upload a Contract for Analysis</CardTitle>
              <CardDescription>
                Upload a PDF contract and LegalMind will analyze it for risks, compliance issues, and key terms.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Dropzone */}
              {!file ? (
                <div
                  {...getRootProps()}
                  className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors
                    ${isDragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/25 hover:border-primary'}`}
                >
                  <input {...getInputProps()} />
                  <Upload className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <p className="text-lg font-medium mb-2">
                    {isDragActive ? 'Drop the file here' : 'Drag & drop a PDF contract'}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    or click to browse (max 50MB)
                  </p>
                </div>
              ) : (
                <div className="border rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <FileText className="h-10 w-10 text-primary" />
                      <div>
                        <p className="font-medium">{file.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {(file.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                    </div>
                    {!uploading && (
                      <Button variant="ghost" size="icon" onClick={removeFile}>
                        <X className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              )}

              {/* Title Input */}
              {file && (
                <div className="space-y-2">
                  <Label htmlFor="title">Contract Title</Label>
                  <Input
                    id="title"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="Enter a title for this contract"
                    disabled={uploading}
                  />
                </div>
              )}

              {/* Progress */}
              {uploading && (
                <div className="space-y-2">
                  <Progress value={progress} />
                  <p className="text-sm text-center text-muted-foreground">
                    {progress < 30 && 'Uploading file...'}
                    {progress >= 30 && progress < 70 && 'Processing contract...'}
                    {progress >= 70 && progress < 100 && 'Preparing analysis...'}
                    {progress === 100 && 'Redirecting...'}
                  </p>
                </div>
              )}

              {/* Error */}
              {error && (
                <div className="bg-destructive/10 text-destructive rounded-lg p-4">
                  {error}
                </div>
              )}

              {/* Submit */}
              <Button
                onClick={handleUpload}
                disabled={!file || uploading}
                className="w-full"
                size="lg"
              >
                {uploading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="h-4 w-4 mr-2" />
                    Upload & Analyze
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
```

---

## 4. New Components

### 4.1 Risk Badge (`components/risk-badge.tsx`)

```tsx
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface RiskBadgeProps {
  score: number | null | undefined;
  showScore?: boolean;
  className?: string;
}

export function RiskBadge({ score, showScore = true, className }: RiskBadgeProps) {
  if (score === null || score === undefined) {
    return <Badge variant="outline" className={className}>Not Assessed</Badge>;
  }

  let level: string;
  let variant: 'default' | 'secondary' | 'destructive' | 'outline';
  let bgColor: string;

  if (score <= 25) {
    level = 'Low';
    variant = 'default';
    bgColor = 'bg-green-500 hover:bg-green-600';
  } else if (score <= 50) {
    level = 'Medium';
    variant = 'secondary';
    bgColor = 'bg-amber-500 hover:bg-amber-600 text-white';
  } else if (score <= 75) {
    level = 'High';
    variant = 'destructive';
    bgColor = 'bg-red-500 hover:bg-red-600';
  } else {
    level = 'Critical';
    variant = 'destructive';
    bgColor = 'bg-red-900 hover:bg-red-950';
  }

  return (
    <Badge className={cn(bgColor, className)}>
      {level}
      {showScore && ` (${score})`}
    </Badge>
  );
}
```

### 4.2 Compliance Checklist (`components/compliance-checklist.tsx`)

```tsx
import { CheckCircle2, XCircle, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface ComplianceItem {
  regulation: string;
  requirement: string;
  status: 'compliant' | 'non-compliant' | 'partial';
  details?: string;
}

interface ComplianceChecklistProps {
  items: ComplianceItem[];
  title?: string;
}

export function ComplianceChecklist({ items, title = 'Compliance Status' }: ComplianceChecklistProps) {
  const getIcon = (status: string) => {
    switch (status) {
      case 'compliant':
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case 'non-compliant':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <AlertCircle className="h-5 w-5 text-amber-500" />;
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {items.map((item, index) => (
            <div
              key={index}
              className="flex items-start gap-3 p-3 rounded-lg bg-muted/50"
            >
              {getIcon(item.status)}
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <span className="font-medium">{item.requirement}</span>
                  <span className="text-sm text-muted-foreground">{item.regulation}</span>
                </div>
                {item.details && (
                  <p className="text-sm text-muted-foreground mt-1">{item.details}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
```

---

## 5. API Routes

### 5.1 Chat Route (`app/api/chat/route.ts`)

```typescript
import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    const response = await fetch(`${BACKEND_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Chat API error:', error);
    return NextResponse.json(
      { status: 'error', error: 'Failed to connect to backend' },
      { status: 500 }
    );
  }
}
```

### 5.2 Contracts Route (`app/api/contracts/route.ts`)

```typescript
import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const response = await fetch(
      `${BACKEND_URL}/api/contracts?${searchParams.toString()}`
    );
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Contracts API error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch contracts' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    
    const response = await fetch(`${BACKEND_URL}/api/contracts`, {
      method: 'POST',
      body: formData,
    });

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Contract upload error:', error);
    return NextResponse.json(
      { error: 'Failed to upload contract' },
      { status: 500 }
    );
  }
}
```

---

## 6. Styling Updates

### 6.1 Updated App Sidebar (`components/app-sidebar.tsx`)

Update the navigation items:

```tsx
const navItems = [
  {
    title: 'Chat',
    url: '/chat',
    icon: MessageSquare,
  },
  {
    title: 'Contracts',
    url: '/contracts',
    icon: FileText,
  },
  {
    title: 'Dashboard',
    url: '/dashboard',
    icon: LayoutDashboard,
  },
  {
    title: 'Documents',
    url: '/documents',
    icon: File,
  },
  {
    title: 'Thinking Logs',
    url: '/thinking-logs',
    icon: Brain,
  },
];
```

### 6.2 Theme Updates

Update the branding in relevant components:
- Logo: Scale icon (⚖️) or custom legal icon
- Name: "LegalMind"
- Colors: Professional blue/gray legal theme
