import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface MarkdownPopupProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  markdownContent: string;
}

const MarkdownPopup = ({ isOpen, onClose, title, markdownContent }: MarkdownPopupProps) => {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[60vw] h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>
            Conteúdo detalhado em formato Markdown.
          </DialogDescription>
        </DialogHeader>
        <div className="flex-grow overflow-y-auto p-4 border rounded-md prose prose-sm max-w-none">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{markdownContent}</ReactMarkdown>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default MarkdownPopup;