export default function ReviewActions() {
  return (
    <div className="review-actions" aria-label="Review actions">
      <button type="button">Approve</button>
      <button type="button">Edit</button>
      <button type="button" className="danger">
        Reject
      </button>
    </div>
  );
}
