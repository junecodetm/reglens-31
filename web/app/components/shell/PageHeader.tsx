"use client";

interface PageHeaderProps {
  title: string;
  kicker?: string;
  lede?: string;
}

export function PageHeader({ title, kicker, lede }: PageHeaderProps) {
  return (
    <header className="page-header">
      {kicker ? <span className="page-header-kicker">{kicker}</span> : null}
      <h1 tabIndex={-1}>{title}</h1>
      {lede ? <p className="page-header-lede">{lede}</p> : null}
    </header>
  );
}
