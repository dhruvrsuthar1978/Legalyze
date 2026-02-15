import { Link } from 'react-router-dom';

function Footer() {
  return (
    <footer className="mt-auto" style={{ backgroundColor: 'var(--color-neutral-900)', borderTop: 'var(--border-thin) solid var(--color-neutral-800)' }}>
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10">
          <div>
            <div className="flex items-center gap-3 mb-5">
              <div className="w-10 h-10 bg-gradient-to-br from-[var(--color-primary-600)] to-[var(--color-accent-blue)] rounded-xl flex items-center justify-center shadow-lg">
                <span className="text-white font-bold text-xl">L</span>
              </div>
              <span className="text-xl font-bold text-white">Legalyze</span>
            </div>
            <p className="text-sm leading-relaxed" style={{ color: 'var(--color-neutral-400)' }}>
              AI-Powered Legal Contract Analysis Made Simple
            </p>
          </div>

          <div>
            <h3 className="font-bold text-white mb-4 text-sm uppercase tracking-wider">Features</h3>
            <ul className="space-y-3 text-sm" style={{ color: 'var(--color-neutral-400)' }}>
              <li><Link to="/features/clause-extraction" className="hover:text-white smooth-transition">Clause Extraction</Link></li>
              <li><Link to="/features/risk-detection" className="hover:text-white smooth-transition">Risk Detection</Link></li>
              <li><Link to="/features/ai-suggestions" className="hover:text-white smooth-transition">AI Suggestions</Link></li>
              <li><Link to="/features/digital-signatures" className="hover:text-white smooth-transition">Digital Signatures</Link></li>
            </ul>
          </div>

          <div>
            <h3 className="font-bold text-white mb-4 text-sm uppercase tracking-wider">Company</h3>
            <ul className="space-y-3 text-sm" style={{ color: 'var(--color-neutral-400)' }}>
              <li><Link to="/about" className="hover:text-white smooth-transition">About Us</Link></li>
              <li><Link to="/contact" className="hover:text-white smooth-transition">Contact</Link></li>
              <li><Link to="/careers" className="hover:text-white smooth-transition">Careers</Link></li>
            </ul>
          </div>

          <div>
            <h3 className="font-bold text-white mb-4 text-sm uppercase tracking-wider">Legal</h3>
            <ul className="space-y-3 text-sm" style={{ color: 'var(--color-neutral-400)' }}>
              <li><Link to="/privacy" className="hover:text-white smooth-transition">Privacy Policy</Link></li>
              <li><Link to="/terms" className="hover:text-white smooth-transition">Terms of Service</Link></li>
              <li><Link to="/security" className="hover:text-white smooth-transition">Security</Link></li>
            </ul>
          </div>
        </div>

        <div className="mt-10 pt-8 text-center text-sm" style={{ borderTop: 'var(--border-thin) solid var(--color-neutral-800)', color: 'var(--color-neutral-500)' }}>
          <p>&copy; {new Date().getFullYear()} Legalyze. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}

export default Footer;