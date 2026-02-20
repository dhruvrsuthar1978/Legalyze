import { Link } from 'react-router-dom';
import { ShieldCheck, Search, FileCheck, PenTool, ArrowRight, Clock, CheckCircle, Workflow } from 'lucide-react';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import Navbar from '../components/layout/Navbar';
import Footer from '../components/layout/Footer';

function LandingPage() {
  const useCases = ['NDA', 'Employment', 'Vendor', 'Service Agreement'];

  const features = [
    {
      icon: Search,
      title: 'Clause Extraction',
      description: 'Automatically identify and extract key clauses from legal contracts.',
    },
    {
      icon: ShieldCheck,
      title: 'Risk Detection',
      description: 'Detect potential risks and vulnerabilities before signing.',
    },
    {
      icon: FileCheck,
      title: 'AI Suggestions',
      description: 'Get recommendations to improve terms and reduce liability.',
    },
    {
      icon: PenTool,
      title: 'Digital Signatures',
      description: 'Sign contracts digitally with a simple end-to-end workflow.',
    },
  ];

  const steps = [
    { number: '1', title: 'Upload Contract', description: 'Upload your PDF or DOCX document.' },
    { number: '2', title: 'Run Analysis', description: 'AI reviews clauses, risks, and compliance points.' },
    { number: '3', title: 'Review Results', description: 'Read summaries and suggestions in plain English.' },
    { number: '4', title: 'Take Action', description: 'Approve edits, compare versions, or move to signature.' },
  ];

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--color-bg-secondary)' }}>
      <Navbar />

      <main>
        {/* Hero Section */}
        <section className="max-w-6xl mx-auto px-6 py-24 text-center">
          <div className="inline-flex items-center px-4 py-2 rounded-full text-sm font-medium mb-6" style={{ backgroundColor: 'var(--color-accent-teal)', color: 'white' }}>
            Built for legal teams and founders
          </div>
          <h1 className="text-5xl md:text-6xl font-bold mb-6 tracking-tight">
            Simple AI Contract Review
          </h1>
          <p className="text-xl max-w-2xl mx-auto mb-12" style={{ color: 'var(--color-text-tertiary)' }}>
            Analyze contracts, detect risks, and get practical suggestions in one place.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-20">
            <Link to="/register">
              <Button size="lg" className="px-8 py-4 text-base">Get Started</Button>
            </Link>
            <Link to="/upload">
              <Button size="lg" variant="outline" className="px-8 py-4 text-base">Upload Contract</Button>
            </Link>
          </div>

          {/* Feature Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            <Card className="p-8 text-left" style={{ backgroundColor: 'var(--color-bg-primary)' }}>
              <div className="flex items-center gap-3 mb-3">
                <Clock className="w-5 h-5" style={{ color: 'var(--color-accent-sky)' }} />
                <p className="text-sm font-medium" style={{ color: 'var(--color-text-tertiary)' }}>
                  Average analysis time
                </p>
              </div>
              <p className="text-3xl font-bold">Under 20s</p>
            </Card>
            <Card className="p-8 text-left" style={{ backgroundColor: 'var(--color-bg-primary)' }}>
              <div className="flex items-center gap-3 mb-3">
                <CheckCircle className="w-5 h-5" style={{ color: 'var(--color-accent-sky)' }} />
                <p className="text-sm font-medium" style={{ color: 'var(--color-text-tertiary)' }}>
                  Plain-English summaries
                </p>
              </div>
              <p className="text-3xl font-bold">Actionable</p>
            </Card>
            <Card className="p-8 text-left" style={{ backgroundColor: 'var(--color-bg-primary)' }}>
              <div className="flex items-center gap-3 mb-3">
                <Workflow className="w-5 h-5" style={{ color: 'var(--color-accent-sky)' }} />
                <p className="text-sm font-medium" style={{ color: 'var(--color-text-tertiary)' }}>
                  From review to signature
                </p>
              </div>
              <p className="text-3xl font-bold">One workflow</p>
            </Card>
          </div>
        </section>

        {/* Use Cases Section */}
        <section className="max-w-6xl mx-auto px-6 pb-16">
          <div className="flex flex-wrap justify-center gap-2 mb-12">
            {useCases.map((item) => (
              <span
                key={item}
                className="px-4 py-2 text-sm font-medium rounded-full border"
                style={{ borderColor: 'var(--color-neutral-300)', color: 'var(--color-text-secondary)', backgroundColor: 'var(--color-bg-primary)' }}
              >
                {item}
              </span>
            ))}
          </div>

          <Card className="max-w-4xl mx-auto p-6 text-left">
            <div className="flex items-center justify-between gap-4 mb-5">
              <p className="text-lg font-semibold">Live analysis preview</p>
              <span className="text-xs px-3 py-1.5 rounded-full font-medium" style={{ backgroundColor: 'var(--color-success-light)', color: 'var(--color-success)' }}>
                Completed
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 rounded-lg" style={{ backgroundColor: 'var(--color-bg-secondary)' }}>
                <p className="text-xs mb-2 font-medium" style={{ color: 'var(--color-text-tertiary)' }}>Document</p>
                <p className="font-semibold">MSA_2026.pdf</p>
              </div>
              <div className="p-4 rounded-lg" style={{ backgroundColor: 'var(--color-bg-secondary)' }}>
                <p className="text-xs mb-2 font-medium" style={{ color: 'var(--color-text-tertiary)' }}>Clauses extracted</p>
                <p className="font-semibold">28 clauses</p>
              </div>
              <div className="p-4 rounded-lg" style={{ backgroundColor: 'var(--color-bg-secondary)' }}>
                <p className="text-xs mb-2 font-medium" style={{ color: 'var(--color-text-tertiary)' }}>Risk level</p>
                <p className="font-semibold">Medium (3 items)</p>
              </div>
            </div>
          </Card>
        </section>

        <section className="max-w-6xl mx-auto px-6 pb-16">
          <h2 className="text-3xl font-bold mb-8 text-center">Core Features</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {features.map((feature) => {
              const Icon = feature.icon;
              return (
                <Card key={feature.title} className="p-6">
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 rounded-md flex items-center justify-center" style={{ backgroundColor: 'var(--color-primary-100)' }}>
                      <Icon className="w-5 h-5" style={{ color: 'var(--color-primary-600)' }} />
                    </div>
                    <div>
                      <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                      <p style={{ color: 'var(--color-text-tertiary)' }}>{feature.description}</p>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        </section>

        <section className="max-w-6xl mx-auto px-6 pb-20">
          <h2 className="text-3xl font-bold mb-8 text-center">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {steps.map((step) => (
              <Card key={step.number} className="p-6">
                <div className="flex items-start gap-4">
                  <div className="w-9 h-9 rounded-md flex items-center justify-center text-white font-semibold" style={{ backgroundColor: 'var(--color-primary-600)' }}>
                    {step.number}
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold mb-1">{step.title}</h3>
                    <p style={{ color: 'var(--color-text-tertiary)' }}>{step.description}</p>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </section>

        <section className="max-w-6xl mx-auto px-6 pb-16">
          <h2 className="text-3xl font-bold mb-8 text-center">Trusted by Legal Teams</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="p-6">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-full flex items-center justify-center" style={{ backgroundColor: 'var(--color-primary-100)' }}>
                  <span className="text-xl font-bold" style={{ color: 'var(--color-primary-600)' }}>JD</span>
                </div>
                <div>
                  <p className="mb-3" style={{ color: 'var(--color-text-tertiary)' }}>
                    "Legalyze cut our contract review time by 60%. The AI suggestions are incredibly accurate and save us hours of manual work."
                  </p>
                  <p className="font-semibold">Jane Doe</p>
                  <p className="text-sm" style={{ color: 'var(--color-text-tertiary)' }}>General Counsel, TechCorp</p>
                </div>
              </div>
            </Card>
            <Card className="p-6">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-full flex items-center justify-center" style={{ backgroundColor: 'var(--color-primary-100)' }}>
                  <span className="text-xl font-bold" style={{ color: 'var(--color-primary-600)' }}>MS</span>
                </div>
                <div>
                  <p className="mb-3" style={{ color: 'var(--color-text-tertiary)' }}>
                    "As a startup founder, I needed a fast way to review vendor agreements. Legalyze gives me confidence without the legal fees."
                  </p>
                  <p className="font-semibold">Michael Smith</p>
                  <p className="text-sm" style={{ color: 'var(--color-text-tertiary)' }}>CEO, StartupHub</p>
                </div>
              </div>
            </Card>
            <Card className="p-6">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-full flex items-center justify-center" style={{ backgroundColor: 'var(--color-primary-100)' }}>
                  <span className="text-xl font-bold" style={{ color: 'var(--color-primary-600)' }}>RL</span>
                </div>
                <div>
                  <p className="mb-3" style={{ color: 'var(--color-text-tertiary)' }}>
                    "The risk detection feature helped us identify problematic clauses we would have missed. It's like having an extra lawyer on the team."
                  </p>
                  <p className="font-semibold">Rebecca Lee</p>
                  <p className="text-sm" style={{ color: 'var(--color-text-tertiary)' }}>Legal Director, FinanceFlow</p>
                </div>
              </div>
            </Card>
          </div>
        </section>

        <section className="max-w-6xl mx-auto px-6 pb-16">
          <h2 className="text-3xl font-bold mb-8 text-center">Frequently Asked Questions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-2">How accurate is the AI analysis?</h3>
              <p style={{ color: 'var(--color-text-tertiary)' }}>
                Our AI is trained on millions of legal documents and achieves 95%+ accuracy in clause identification. However, we always recommend having a legal professional review critical contracts.
              </p>
            </Card>
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-2">Is my data secure?</h3>
              <p style={{ color: 'var(--color-text-tertiary)' }}>
                Absolutely. We use bank-level encryption and never share your documents. All data is stored securely and you maintain full ownership of your contracts.
              </p>
            </Card>
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-2">What file formats do you support?</h3>
              <p style={{ color: 'var(--color-text-tertiary)' }}>
                We support PDF, DOCX, and TXT files. Simply upload your contract and our system will process it automatically within seconds.
              </p>
            </Card>
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-2">Can I try it for free?</h3>
              <p style={{ color: 'var(--color-text-tertiary)' }}>
                Yes! Create a free account and analyze your first 3 contracts at no cost. No credit card required to get started.
              </p>
            </Card>
          </div>
        </section>

        <section className="max-w-4xl mx-auto px-6 pb-20">
          <Card className="p-10 text-center" glass>
            <h2 className="text-3xl font-bold mb-3">Start Reviewing Contracts Faster</h2>
            <p className="mb-6" style={{ color: 'var(--color-text-tertiary)' }}>
              Create an account and run your first analysis in minutes.
            </p>
            <Link to="/register">
              <Button size="lg" className="gap-2">
                Create Free Account
                <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
          </Card>
        </section>
      </main>

      <Footer />
    </div>
  );
}

export default LandingPage;
