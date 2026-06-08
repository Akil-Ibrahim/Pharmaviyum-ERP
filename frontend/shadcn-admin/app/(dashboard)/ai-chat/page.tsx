"use client";

import * as React from "react";
import { api } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

export default function AiChatPage() {
  const [question, setQuestion] = React.useState("");
  const [answer, setAnswer] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setAnswer(null);
    if (!question.trim()) return;
    setLoading(true);
    try {
      const res = await api.post<any>("/rag/ask", { question });
      // backend proxies to Mortarium AI and returns JSON
      setAnswer(res?.answer ?? JSON.stringify(res));
    } catch (err: any) {
      setError(err?.message ?? String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold">Mortarium AI</h1>

      <form onSubmit={handleSubmit} className="space-y-3">
        <Input
          placeholder="Ask Mortarium a short question..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />

        <div className="flex items-center gap-2">
          <Button type="submit" disabled={loading}>
            {loading ? "Asking..." : "Ask"}
          </Button>
          <Button
            type="button"
            variant="ghost"
            onClick={() => {
              setQuestion("");
              setAnswer(null);
              setError(null);
            }}
          >
            Clear
          </Button>
        </div>
      </form>

      {error && (
        <div className="rounded border border-red-400 bg-red-50 p-3 text-sm text-red-700">{error}</div>
      )}

      {answer && (
        <div>
          <h2 className="text-lg font-medium">Answer</h2>
          <Textarea readOnly value={answer} />
        </div>
      )}
    </div>
  );
}
