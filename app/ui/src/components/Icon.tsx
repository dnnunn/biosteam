"use client";
import * as React from 'react';

type IconProps = {
  // Allow either a React component (SVGR) or a Next/image-like object with `src`
  component: React.ComponentType<React.SVGProps<SVGSVGElement>> | any;
  size?: number | string;
  color?: string;
  title?: string;
  className?: string;
  style?: React.CSSProperties;
};

export function Icon({ component: Cmp, size = '1.25rem', color = 'currentColor', title, className, style }: IconProps) {
  // Coerce various possible shapes into a renderable component
  const anyCmp: any = Cmp as any;
  const RenderCmp = typeof anyCmp === 'function'
    ? anyCmp
    : (typeof anyCmp?.default === 'function' ? anyCmp.default : null);

  if (RenderCmp) {
    return (
      <RenderCmp
        role="img"
        aria-hidden={title ? undefined : true}
        title={title}
        width={size}
        height={size}
        // Ensure shapes use the current text color
        fill="currentColor"
        className={className}
        style={{ color, display: 'inline-block', verticalAlign: 'middle', ...style }}
      />
    );
  }

  // Fallback: Treat as an image object or URL string
  const src = typeof anyCmp === 'string' ? anyCmp : anyCmp?.src;
  if (src) {
    return (
      <img
        src={src}
        alt={title || ''}
        width={typeof size === 'number' ? size : undefined}
        height={typeof size === 'number' ? size : undefined}
        className={className}
        style={{ display: 'inline-block', verticalAlign: 'middle', color, ...style }}
      />
    );
  }

  // Last resort: empty span to avoid crashing render
  return <span className={className} style={style} aria-hidden />;
}
