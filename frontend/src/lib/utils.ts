import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Parse a datetime string as UTC, regardless of whether it has timezone info.
 * Python's datetime.now().isoformat() stores naive UTC strings (no 'Z' suffix),
 * which JavaScript incorrectly interprets as local time.
 */
export function parseUTC(dateStr: string): Date {
  if (!dateStr.endsWith('Z') && !dateStr.match(/[+-]\d{2}:\d{2}$/)) {
    return new Date(dateStr + 'Z');
  }
  return new Date(dateStr);
}
