import { useState } from 'react';
import { FileCheck, Download, Sparkles } from 'lucide-react';
import { useDispatch } from 'react-redux';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Select from '../components/ui/Select';
import Input from '../components/ui/Input';
import Textarea from '../components/ui/Textarea';
import { generationService } from '../services/generationService';
import { showToast } from '../store/uiSlice';

function GeneratePage() {
  const dispatch = useDispatch();
  const [contractType, setContractType] = useState('');
  const [party1Name, setParty1Name] = useState('');
  const [party2Name, setParty2Name] = useState('');
  const [duration, setDuration] = useState('');
  const [requirements, setRequirements] = useState('');
  const [generating, setGenerating] = useState(false);
  const [generated, setGenerated] = useState(false);
  const [previewText, setPreviewText] = useState('');

  const contractTypes = [
    { value: 'employment', label: 'Employment Agreement' },
    { value: 'nda', label: 'Non-Disclosure Agreement (NDA)' },
    { value: 'service', label: 'Service Agreement' },
    { value: 'sales', label: 'Sales Contract' },
    { value: 'lease', label: 'Lease Agreement' },
  ];

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const payload = {
        contract_type: contractType,
        party1_name: party1Name,
        party2_name: party2Name,
        duration,
        requirements,
      };
      const res = await generationService.adhocPreview(payload);
      setPreviewText(res.preview_text || '');
      setGenerated(true);
      dispatch(showToast({ type: 'success', title: 'Preview Generated', message: 'Draft preview is ready.' }));
    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Failed to generate preview';
      dispatch(showToast({ type: 'error', title: 'Generation Failed', message }));
    } finally {
      setGenerating(false);
    }
  };

  const downloadPreview = () => {
    const blob = new Blob([previewText || 'No generated preview text.'], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${contractType || 'contract'}_preview.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div className="text-center">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full mb-4" style={{ background: 'var(--glass-bg)', backdropFilter: 'blur(16px)', border: '1px solid var(--glass-border)' }}>
          <Sparkles className="w-4 h-4" style={{ color: 'var(--color-accent-blue)' }} />
          <span className="text-sm font-semibold" style={{ color: 'var(--color-text-primary)' }}>AI-Powered Contract Generation</span>
        </div>
        <h1 className="text-4xl md:text-5xl font-bold mb-4" style={{ color: 'var(--color-text-primary)' }}>Generate Custom Contract</h1>
        <p className="text-lg max-w-2xl mx-auto" style={{ color: 'var(--color-text-tertiary)' }}>
          Generate an AI draft preview from your requirements.
        </p>
      </div>

      <Card className="p-8">
        <div className="space-y-6">
          <Select label="Contract Type" options={contractTypes} value={contractType} onChange={setContractType} placeholder="Select contract type" />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Input label="Party 1 Name" placeholder="e.g., ABC Company Inc." value={party1Name} onChange={(e) => setParty1Name(e.target.value)} />
            <Input label="Party 2 Name" placeholder="e.g., John Smith" value={party2Name} onChange={(e) => setParty2Name(e.target.value)} />
          </div>

          <Input
            label="Contract Duration (months)"
            type="number"
            placeholder="e.g., 12"
            helperText="Leave blank for indefinite contracts"
            value={duration}
            onChange={(e) => setDuration(e.target.value)}
          />

          <Textarea
            rows={8}
            placeholder={`Example:
- Include non-compete clause for 2 years
- Add intellectual property rights transfer
- Specify payment terms
- Include confidentiality obligations`}
            value={requirements}
            onChange={(e) => setRequirements(e.target.value)}
          />

          <Button onClick={handleGenerate} className="w-full gap-2 glow" size="lg" loading={generating} disabled={!contractType}>
            <FileCheck className="w-5 h-5" style={{ color: 'white' }} />
            {generating ? 'Generating Preview...' : 'Generate Contract Preview'}
          </Button>
        </div>
      </Card>

      {generated && (
        <Card className="p-8">
          <div className="space-y-6">
            <div className="flex items-center gap-4 p-4 rounded-2xl" style={{ background: 'var(--color-success-light)' }}>
              <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ background: 'var(--color-success)' }}>
                <FileCheck className="w-6 h-6" style={{ color: 'white' }} />
              </div>
              <div>
                <h2 className="text-xl font-bold" style={{ color: 'var(--color-success)' }}>Preview Generated</h2>
                <p className="text-sm" style={{ color: 'var(--color-success)' }}>Review and download your generated draft text</p>
              </div>
            </div>

            <div className="p-6 rounded-xl border max-h-96 overflow-y-auto" style={{ backgroundColor: 'var(--color-bg-tertiary)', borderColor: 'var(--color-neutral-200)' }}>
              <p className="text-sm whitespace-pre-line" style={{ color: 'var(--color-text-secondary)' }}>
                {previewText || 'No preview text returned by backend.'}
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-3">
              <Button className="flex-1 gap-2" onClick={downloadPreview}>
                <Download className="w-4 h-4" style={{ color: 'white' }} />
                Download Preview TXT
              </Button>
              <Button variant="ghost" onClick={() => setGenerated(false)}>Generate Another</Button>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}

export default GeneratePage;
