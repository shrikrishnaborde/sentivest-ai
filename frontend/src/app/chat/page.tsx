import { ChatInterface } from "@/components/ChatInterface";

export default function ChatPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Ask SentiVest</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Ask natural-language questions about any tracked stock. Every answer is grounded in
          retrieved, cited sources.
        </p>
      </div>
      <ChatInterface />
    </div>
  );
}
