type HelpHintProps = {
  text: string;
};

export default function HelpHint({ text }: HelpHintProps) {
  return (
    <span className="help-hint" tabIndex={0} aria-label={text}>
      <span className="help-hint-badge" aria-hidden="true">
        ?
      </span>
      <span className="help-hint-tooltip" role="tooltip">
        {text}
      </span>
    </span>
  );
}
