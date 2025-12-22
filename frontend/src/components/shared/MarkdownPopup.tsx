import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
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
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-[70vw] h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>
        <div className="flex-grow overflow-y-auto px-6 py-4 bg-gray-50 rounded-md">
          <article className="markdown-content">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{markdownContent}</ReactMarkdown>
          </article>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default MarkdownPopup;
