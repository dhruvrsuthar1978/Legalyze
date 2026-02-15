import { useState } from 'react';
import { FileCheck, Download, Sparkles } from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Select from '../components/ui/Select';
import Input from '../components/ui/Input';
import Textarea from '../components/ui/Textarea';

function GeneratePage() {
  const [contractType, setContractType] = useState('');
  const [party1Name, setParty1Name] = useState('');
  const [party2Name, setParty2Name] = useState('');
  const [duration, setDuration] = useState('');
  const [requirements, setRequirements] = useState('');
  const [generating, setGenerating] = useState(false);
  const [generated, setGenerated] = useState(false);

  const contractTypes = [
    { value: 'employment', label: 'Employment Agreement' },
    { value: 'nda', label: 'Non-Disclosure Agreement (NDA)' },
    { value: 'service', label: 'Service Agreement' },
    { value: 'sales', label: 'Sales Contract' },
    { value: 'lease', label: 'Lease Agreement' },
  ];

  const handleGenerate = () => {
    setGenerating(true);
    setTimeout(() => {
      setGenerating(false);
      setGenerated(true);
    }, 2000);
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full mb-4" style={{ background: 'var(--glass-bg)', backdropFilter: 'blur(16px)', border: '1px solid var(--glass-border)' }}>
          <Sparkles className="w-4 h-4" style={{ color: 'var(--color-accent-blue)' }} />
          <span className="text-sm font-semibold" style={{ color: 'var(--color-text-primary)' }}>AI-Powered Contract Generation</span>
        </div>
        <h1 className="text-4xl md:text-5xl font-bold mb-4" style={{ color: 'var(--color-text-primary)' }}>Generate Custom Contract</h1>
        <p className="text-lg max-w-2xl mx-auto" style={{ color: 'var(--color-text-tertiary)' }}>
          Tell us what you need and our AI will create a balanced, legally sound contract tailored to your requirements
        </p>
      </div>

      {/* Form */}
      <Card className="p-8">
        <div className="space-y-6">
          {/* Contract Type */}
          <Select
            label="Contract Type"
            options={contractTypes}
            value={contractType}
            onChange={setContractType}
            placeholder="Select contract type"
          />

          {/* Basic Details - Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Input
              label="Party 1 Name"
              placeholder="e.g., ABC Company Inc."
              value={party1Name}
              onChange={(e) => setParty1Name(e.target.value)}
            />

            <Input
              label="Party 2 Name"
              placeholder="e.g., John Smith"
              value={party2Name}
              onChange={(e) => setParty2Name(e.target.value)}
            />
          </div>

          <Input
            label="Contract Duration (months)"
            type="number"
            placeholder="e.g., 12"
            helperText="Leave blank for indefinite contracts"
            value={duration}
            onChange={(e) => setDuration(e.target.value)}
          />

          {/* Custom Requirements - Featured */}
          <div className="p-6 rounded-2xl" style={{ background: 'linear-gradient(135deg, var(--color-primary-50), var(--color-accent-sky)/10)', border: '2px solid var(--color-primary-200)' }}>
            <div className="flex items-start gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0" style={{ background: 'linear-gradient(135deg, var(--color-primary-500), var(--color-accent-blue))' }}>
                <Sparkles className="w-5 h-5" style={{ color: 'white' }} />
              </div>
              <div>
                <h3 className="text-lg font-bold mb-1" style={{ color: 'var(--color-text-primary)' }}>
                  Custom Requirements & Clauses
                </h3>
                <p className="text-sm" style={{ color: 'var(--color-text-tertiary)' }}>
                  Describe what you want included in the contract. Be specific about terms, conditions, and special provisions.
                </p>
              </div>
            </div>
            
            <Textarea
              rows={8}
              placeholder="Example: 
• Include non-compete clause for 2 years
• Add intellectual property rights transfer
• Specify payment terms: 50% upfront, 50% on completion
• Include confidentiality obligations
• Add termination clause with 30 days notice
• Include dispute resolution through arbitration
• Specify work location as remote
• Add performance milestones and deliverables"
              value={requirements}
              onChange={(e) => setRequirements(e.target.value)}
              className="mt-3"
            />
          </div>

          {/* Generate Button */}
          <Button 
            onClick={handleGenerate} 
            className="w-full gap-2 glow"
            size="lg"
            loading={generating}
            disabled={!contractType}
          >
            <FileCheck className="w-5 h-5" style={{ color: 'white' }} />
            {generating ? 'Generating Contract...' : 'Generate Balanced Contract'}
          </Button>
        </div>
      </Card>

      {/* Generated Contract Preview */}
      {generated && (
        <Card className="p-8">
          <div className="space-y-6">
            {/* Success Header */}
            <div className="flex items-center gap-4 p-4 rounded-2xl" style={{ background: 'var(--color-success-light)' }}>
              <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ background: 'var(--color-success)' }}>
                <FileCheck className="w-6 h-6" style={{ color: 'white' }} />
              </div>
              <div>
                <h2 className="text-xl font-bold" style={{ color: 'var(--color-success)' }}>Contract Generated Successfully!</h2>
                <p className="text-sm" style={{ color: 'var(--color-success)' }}>Your custom contract is ready for review and download</p>
              </div>
            </div>

            {/* Contract Details */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 rounded-xl" style={{ background: 'var(--color-bg-tertiary)' }}>
                <p className="text-xs font-semibold uppercase tracking-wider mb-1" style={{ color: 'var(--color-text-tertiary)' }}>Contract Type</p>
                <p className="text-lg font-bold" style={{ color: 'var(--color-text-primary)' }}>
                  {contractTypes.find(ct => ct.value === contractType)?.label}
                </p>
              </div>
              <div className="p-4 rounded-xl" style={{ background: 'var(--color-bg-tertiary)' }}>
                <p className="text-xs font-semibold uppercase tracking-wider mb-1" style={{ color: 'var(--color-text-tertiary)' }}>Parties</p>
                <p className="text-lg font-bold" style={{ color: 'var(--color-text-primary)' }}>
                  {party1Name || 'Party 1'} & {party2Name || 'Party 2'}
                </p>
              </div>
              <div className="p-4 rounded-xl" style={{ background: 'var(--color-bg-tertiary)' }}>
                <p className="text-xs font-semibold uppercase tracking-wider mb-1" style={{ color: 'var(--color-text-tertiary)' }}>Duration</p>
                <p className="text-lg font-bold" style={{ color: 'var(--color-text-primary)' }}>
                  {duration ? `${duration} months` : 'Indefinite'}
                </p>
              </div>
            </div>

            {/* Preview */}
            <div>
              <h3 className="text-lg font-bold mb-3" style={{ color: 'var(--color-text-primary)' }}>Contract Preview</h3>
              <div className="p-6 rounded-xl border max-h-96 overflow-y-auto" style={{ backgroundColor: 'var(--color-bg-tertiary)', borderColor: 'var(--color-neutral-200)' }}>
                <div className="space-y-4 text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                  <p className="font-bold text-center text-lg">EMPLOYMENT AGREEMENT</p>
                  <p>This Employment Agreement ("Agreement") is entered into on [Date] between {party1Name || '[Party 1]'} ("Employer") and {party2Name || '[Party 2]'} ("Employee").</p>
                  <p className="font-semibold">1. POSITION AND DUTIES</p>
                  <p>The Employee is hired as [Position] and will perform duties as reasonably assigned by the Employer...</p>
                  <p className="font-semibold">2. COMPENSATION</p>
                  <p>The Employee will receive an annual salary of $[Amount], paid bi-weekly...</p>
                  <p className="font-semibold">3. BENEFITS</p>
                  <p>The Employee will be entitled to standard benefits including health insurance, paid time off...</p>
                  <p className="font-semibold">4. TERMINATION</p>
                  <p>Either party may terminate this agreement with {duration || 30} days written notice...</p>
                  {requirements && (
                    <>
                      <p className="font-semibold">5. CUSTOM PROVISIONS</p>
                      <p className="whitespace-pre-line">{requirements}</p>
                    </>
                  )}
                  <p className="text-center mt-8" style={{ color: 'var(--color-text-tertiary)' }}>[Additional clauses...]</p>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-3">
              <Button className="flex-1 gap-2">
                <Download className="w-4 h-4" style={{ color: 'white' }} />
                Download PDF
              </Button>
              <Button variant="outline" className="flex-1 gap-2">
                <Download className="w-4 h-4" style={{ color: 'var(--color-primary-600)' }} />
                Download DOCX
              </Button>
              <Button variant="ghost" onClick={() => setGenerated(false)}>
                Generate Another
              </Button>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}

export default GeneratePage;