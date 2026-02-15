import { Link } from 'react-router-dom';
import { ShieldCheck, Search, FileCheck, PenTool, Upload, ArrowRight, Sparkles, Zap, TrendingUp, CheckCircle2, Star } from 'lucide-react';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import Navbar from '../components/layout/Navbar';
import Footer from '../components/layout/Footer';

function LandingPage() {
  const features = [
    {
      icon: Search,
      title: 'Clause Extraction',
      description: 'Automatically identify and extract key clauses from legal contracts with AI precision.',
    },
    {
      icon: ShieldCheck,
      title: 'Risk Detection',
      description: 'Detect potential risks and vulnerabilities in your contracts before signing.',
    },
    {
      icon: FileCheck,
      title: 'AI Suggestions',
      description: 'Get intelligent recommendations to improve contract terms and reduce liability.',
    },
    {
      icon: PenTool,
      title: 'Digital Signatures',
      description: 'Securely sign contracts digitally with legally binding electronic signatures.',
    },
  ];

  const steps = [
    { number: '01', title: 'Upload Contract', description: 'Upload your PDF or DOCX contract document' },
    { number: '02', title: 'AI Analysis', description: 'Our AI analyzes clauses, risks, and compliance' },
    { number: '03', title: 'Review Results', description: 'Get plain English explanations and suggestions' },
    { number: '04', title: 'Take Action', description: 'Accept suggestions or generate balanced contracts' },
  ];

  return (
    <div className="min-h-screen overflow-hidden">
      <div className="aurora-bg min-h-screen">
        <Navbar />

        {/* Hero Section - Floating UI Cards */}
        <section className="relative max-w-7xl mx-auto px-6 pt-20 pb-32">
          {/* Animated gradient orbs */}
          <div className="absolute top-20 left-10 w-96 h-96 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob" style={{ background: 'var(--color-primary-400)' }}></div>
          <div className="absolute top-40 right-10 w-96 h-96 rounded-full mix-blend-multiply filter blur-3xl opacity-15 animate-blob animation-delay-2000" style={{ background: 'var(--color-accent-purple)' }}></div>
          <div className="absolute bottom-0 left-1/2 w-96 h-96 rounded-full mix-blend-multiply filter blur-3xl opacity-15 animate-blob animation-delay-4000" style={{ background: 'var(--color-accent-teal)' }}></div>

          <div className="relative z-10 text-center">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full mb-8" style={{ background: 'var(--glass-bg)', backdropFilter: 'blur(16px)', border: '1px solid var(--glass-border)' }}>
              <Sparkles className="w-4 h-4" style={{ color: 'var(--color-accent-blue)' }} />
              <span className="text-sm font-semibold" style={{ color: 'var(--color-text-primary)' }}>Powered by GPT-4 AI</span>
            </div>

            {/* Headline */}
            <h1 className="text-5xl md:text-7xl lg:text-8xl font-bold mb-8 max-w-5xl mx-auto leading-tight">
              Legal Contract Analysis,
              <br />
              <span className="gradient-text-animated inline-block mt-2">
                Powered by AI
              </span>
            </h1>

            {/* Subheadline */}
            <p className="text-xl md:text-2xl mb-12 max-w-3xl mx-auto font-medium" style={{ color: 'var(--color-text-tertiary)' }}>
              Extract clauses, detect risks, and generate balanced contracts in seconds. 
              <br className="hidden md:block" />
              Enterprise-grade AI trusted by legal professionals.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-20">
              <Link to="/register">
                <Button size="xl" className="gap-3 shadow-2xl glow group">
                  Start Analyzing Free
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" style={{ color: 'white' }} />
                </Button>
              </Link>
              <Link to="/upload">
                <Button size="xl" variant="outline" className="gap-3 backdrop-blur-sm">
                  <Upload className="w-5 h-5" style={{ color: 'var(--color-primary-600)' }} />
                  Upload Contract
                </Button>
              </Link>
            </div>

            {/* Floating UI Cards */}
            <div className="relative max-w-6xl mx-auto">
              {/* Main preview */}
              <div className="glass-card rounded-3xl p-8 shadow-2xl animate-float">
                <div className="rounded-2xl overflow-hidden" style={{ background: 'var(--color-bg-secondary)' }}>
                  <div className="flex items-center gap-2 px-6 py-4" style={{ borderBottom: '1px solid var(--color-neutral-200)' }}>
                    <div className="w-3 h-3 rounded-full" style={{ background: '#EF4444' }}></div>
                    <div className="w-3 h-3 rounded-full" style={{ background: '#F59E0B' }}></div>
                    <div className="w-3 h-3 rounded-full" style={{ background: '#10B981' }}></div>
                  </div>
                  <div className="p-8 space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-xl font-bold mb-1" style={{ color: 'var(--color-text-primary)' }}>Employment Agreement</h3>
                        <p className="text-sm" style={{ color: 'var(--color-text-tertiary)' }}>Analyzed in 12 seconds</p>
                      </div>
                      <div className="px-4 py-2 rounded-full" style={{ background: 'var(--color-success-light)', color: 'var(--color-success)' }}>
                        <span className="text-sm font-bold">Low Risk</span>
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-4">
                      {[
                        { label: 'Clauses', value: '24' },
                        { label: 'AI Score', value: '94%' },
                        { label: 'Risks', value: '2' }
                      ].map((stat, i) => (
                        <div key={i} className="p-4 rounded-xl text-center" style={{ background: 'var(--color-bg-tertiary)' }}>
                          <div className="text-3xl font-bold mb-1" style={{ color: 'var(--color-primary-600)' }}>{stat.value}</div>
                          <div className="text-sm" style={{ color: 'var(--color-text-tertiary)' }}>{stat.label}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Floating cards */}
              <div className="hidden lg:block absolute -top-8 -left-12 glass-card rounded-2xl p-4 shadow-xl animate-float animation-delay-2000" style={{ width: '200px' }}>
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'var(--color-success-light)' }}>
                    <CheckCircle2 className="w-6 h-6" style={{ color: 'var(--color-success)' }} />
                  </div>
                  <span className="text-sm font-bold" style={{ color: 'var(--color-text-primary)' }}>AI Verified</span>
                </div>
                <p className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>All clauses reviewed for compliance</p>
              </div>

              <div className="hidden lg:block absolute -top-16 -right-12 glass-card rounded-2xl p-4 shadow-xl animate-float animation-delay-4000" style={{ width: '220px' }}>
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'var(--color-primary-100)' }}>
                    <Zap className="w-6 h-6" style={{ color: 'var(--color-primary-600)' }} />
                  </div>
                  <div>
                    <div className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>12s</div>
                    <div className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>Analysis time</div>
                  </div>
                </div>
              </div>

              <div className="hidden lg:block absolute -bottom-4 -right-16 glass-card rounded-2xl p-4 shadow-xl animate-float animation-delay-6000" style={{ width: '180px' }}>
                <div className="flex items-center gap-2 mb-2">
                  {[1,2,3,4,5].map((i) => (
                    <Star key={i} className="w-4 h-4 fill-current" style={{ color: '#F59E0B' }} />
                  ))}
                </div>
                <p className="text-xs font-semibold" style={{ color: 'var(--color-text-primary)' }}>5,000+ happy clients</p>
              </div>
            </div>
          </div>
        </section>

        {/* Features - Bento Grid */}
        <section className="max-w-7xl mx-auto px-6 py-32">
          <div className="text-center mb-20">
            <h2 className="text-5xl md:text-6xl font-bold mb-6">
              Everything you need
              <br />
              <span className="gradient-text-animated">in one platform</span>
            </h2>
            <p className="text-xl max-w-2xl mx-auto" style={{ color: 'var(--color-text-tertiary)' }}>
              Analyze, generate, and manage legal contracts with AI-powered precision
            </p>
          </div>

          {/* Bento Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              const sizes = ['lg:col-span-2 lg:row-span-2', '', '', 'lg:col-span-2'];
              return (
                <div key={index} className={`bento-item group cursor-pointer card-3d ${sizes[index] || ''}`}>
                  <div className="flex flex-col h-full">
                    <div className="w-14 h-14 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300" style={{ background: 'linear-gradient(135deg, var(--color-primary-100), var(--color-primary-200))' }}>
                      <Icon className="w-7 h-7" style={{ color: 'var(--color-primary-600)' }} />
                    </div>
                    <h3 className="text-2xl font-bold mb-3" style={{ color: 'var(--color-text-primary)' }}>{feature.title}</h3>
                    <p className="text-lg leading-relaxed" style={{ color: 'var(--color-text-tertiary)' }}>
                      {feature.description}
                    </p>
                    {index === 0 && (
                      <div className="mt-auto pt-6">
                        <div className="flex items-center gap-2 text-sm font-semibold" style={{ color: 'var(--color-primary-600)' }}>
                          Learn more
                          <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* How It Works - Timeline */}
        <section className="max-w-6xl mx-auto px-6 py-32">
          <div className="text-center mb-20">
            <h2 className="text-5xl md:text-6xl font-bold mb-6">
              From upload to insights
              <br />
              <span className="gradient-text-animated">in seconds</span>
            </h2>
          </div>

          <div className="relative">
            {/* Timeline line */}
            <div className="hidden lg:block absolute left-1/2 top-0 bottom-0 w-0.5 -translate-x-1/2" style={{ background: 'linear-gradient(to bottom, var(--color-primary-300), var(--color-primary-100))' }}></div>

            <div className="space-y-16">
              {steps.map((step, index) => (
                <div key={index} className={`flex flex-col lg:flex-row gap-8 items-center ${index % 2 === 1 ? 'lg:flex-row-reverse' : ''}`}>
                  <div className="flex-1">
                    <div className="bento-item text-left">
                      <div className="w-16 h-16 rounded-2xl flex items-center justify-center mb-6 text-3xl font-bold text-white" style={{ background: 'linear-gradient(135deg, var(--color-primary-600), var(--color-accent-blue))' }}>
                        {step.number}
                      </div>
                      <h3 className="text-2xl font-bold mb-4" style={{ color: 'var(--color-text-primary)' }}>{step.title}</h3>
                      <p className="text-lg leading-relaxed" style={{ color: 'var(--color-text-tertiary)' }}>
                        {step.description}
                      </p>
                    </div>
                  </div>
                  <div className="hidden lg:block w-20 h-20 rounded-full shrink-0" style={{ background: 'linear-gradient(135deg, var(--color-primary-500), var(--color-accent-blue))', boxShadow: '0 0 0 4px var(--color-bg-primary)' }}></div>
                  <div className="flex-1"></div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="max-w-5xl mx-auto px-6 py-32">
          <div className="mesh-gradient rounded-3xl p-12 md:p-20 text-center relative overflow-hidden">
            {/* Decorative elements */}
            <div className="absolute top-0 right-0 w-64 h-64 rounded-full filter blur-3xl opacity-20" style={{ background: 'var(--color-accent-purple)' }}></div>
            <div className="absolute bottom-0 left-0 w-64 h-64 rounded-full filter blur-3xl opacity-20" style={{ background: 'var(--color-accent-teal)' }}></div>
            
            <div className="relative z-10">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full mb-6" style={{ background: 'var(--glass-bg)', backdropFilter: 'blur(16px)', border: '1px solid var(--glass-border)' }}>
                <TrendingUp className="w-4 h-4" style={{ color: 'var(--color-success)' }} />
                <span className="text-sm font-semibold" style={{ color: 'var(--color-text-primary)' }}>Join 5,000+ legal professionals</span>
              </div>
              
              <h2 className="text-4xl md:text-5xl font-bold mb-6 max-w-3xl mx-auto">
                Ready to transform your
                <br />
                contract analysis workflow?
              </h2>
              
              <p className="text-xl mb-10 max-w-2xl mx-auto" style={{ color: 'var(--color-text-secondary)' }}>
                Start analyzing contracts with AI today. No credit card required.
              </p>
              
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link to="/register">
                  <Button size="xl" className="shadow-2xl glow group">
                    Get Started Free
                    <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" style={{ color: 'white' }} />
                  </Button>
                </Link>
                <Link to="/upload">
                  <Button size="xl" variant="outline" className="backdrop-blur-sm">
                    Try Demo
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </section>
      </div>

      <Footer />
    </div>
  );
}

export default LandingPage;