type LeadsListPlaceholderProps = {
  title: string;
};

export function LeadsListPlaceholder({ title }: LeadsListPlaceholderProps) {
  return (
    <div>
      <h2>{title}</h2>
      <p>Lead list component placeholder.</p>
    </div>
  );
}
