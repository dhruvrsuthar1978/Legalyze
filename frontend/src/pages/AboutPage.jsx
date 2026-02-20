import Navbar from '../components/layout/Navbar';
import Footer from '../components/layout/Footer';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';

function AboutPage() {
  const features = [
    'Automated clause extraction and labeling',
    'AI-driven risk and compliance scoring',
    'Context-aware suggestions to improve contract language',
    'Secure digital signatures and sharing',
  ];


  return (
    <div className="min-h-screen">
      <div className="aurora-bg min-h-screen">
        <Navbar />

        <main className="max-w-5xl mx-auto p-6 py-20">
          <Card className="p-8" glass>
            <h1 className="text-4xl font-bold mb-4">About Legalyze</h1>

            <p className="text-lg mb-4" style={{ color: 'var(--color-text-tertiary)' }}>
              Legalyze helps legal teams and individuals move faster and with greater confidence when
              reviewing and negotiating contracts. Our AI surfaces important clauses, highlights
              potential risks, and provides plain-English explanations so outcomes are easier to act on.
            </p>

            <h2 className="text-2xl font-semibold mt-6 mb-2">Our Mission</h2>
            <p className="mb-4">Make contract review accessible, accurate, and efficient by combining
              legal expertise with modern AI. We prioritize clarity, security, and practical workflows.</p>

            <h2 className="text-2xl font-semibold mt-6 mb-2">What We Offer</h2>
            <ul className="list-disc pl-6 mb-4" style={{ color: 'var(--color-text-tertiary)' }}>
              {features.map((f, i) => (
                <li key={i} className="mb-2">{f}</li>
              ))}
            </ul>

            {/* Team section removed as requested */}

            <div className="mt-6 flex flex-col sm:flex-row gap-4 items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold">Work with us</h3>
                <p className="text-sm" style={{ color: 'var(--color-text-tertiary)' }}>
                  Interested in partnering or joining the team? Reach out and we'll get back to you.
                </p>
              </div>

              <div className="flex gap-3">
                <a href="mailto:hello@legalyze.example">
                  <Button variant="outline">Contact Us</Button>
                </a>
                <a href="/register">
                  <Button>Get Started</Button>
                </a>
              </div>
            </div>
          </Card>
        </main>

        <Footer />
      </div>
    </div>
  );
}

export default AboutPage;
