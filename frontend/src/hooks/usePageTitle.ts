import { useEffect } from "react";

export function usePageTitle(title: string) {
  useEffect(() => {
    document.title = `${title} — SwiftSale`;
    return () => {
      document.title = "SwiftSale";
    };
  }, [title]);
}
