function Card({ children, className = '', hover = false, glass = false }) {
  const baseStyles = 'p-6 transition-all duration-300';
  
  const styles = glass 
    ? 'glass-card' 
    : 'bento-item';
  
  const hoverStyles = hover 
    ? 'cursor-pointer' 
    : '';

  return (
    <div className={`${baseStyles} ${styles} ${hoverStyles} ${className}`}>
      {children}
    </div>
  );
}

export default Card;