import { useEffect, useMemo, useState } from 'react';
import { FileCheck, Download, Sparkles, FileText } from 'lucide-react';
import { useDispatch } from 'react-redux';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Select from '../components/ui/Select';
import Input from '../components/ui/Input';
import Textarea from '../components/ui/Textarea';
import { contractService } from '../services/contractService';
import { generationService } from '../services/generationService';
import { showToast } from '../store/uiSlice';

function GeneratePage() {
  const dispatch = useDispatch();
  const [loadingContracts, setLoadingContracts] = useState(true);
  const [contracts, setContracts] = useState([]);
  const [selectedContractId, setSelectedContractId] = useState('');
  const [format, setFormat] = useState('pdf');
  const [includeSummary, setIncludeSummary] = useState(true);
  const [previewing, setPreviewing] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [previewText, setPreviewText] = useState('');
  const [generatedDoc, setGeneratedDoc] = useState(null);
  const [loadingTemplates, setLoadingTemplates] = useState(true);
  const [templates, setTemplates] = useState([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState('');
  const [templatePreviewing, setTemplatePreviewing] = useState(false);
  const [templatePreviewText, setTemplatePreviewText] = useState('');
  const [templateForm, setTemplateForm] = useState({
    party_1_name: '',
    party_2_name: '',
    effective_date: '',
    term_months: '12',
    governing_law: '',
    purpose: '',
    payment_terms: '',
    scope_of_services: '',
    position_title: '',
    base_salary: '',
    termination_notice_days: '30',
    deliverables: '',
    additional_terms: '',
  });

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const response = await contractService.getContracts(0, 100);
        if (!mounted) return;
        setContracts(response.contracts || []);
      } catch (err) {
        if (!mounted) return;
        dispatch(showToast({
          type: 'error',
          title: 'Failed to Load Contracts',
          message: err.response?.data?.detail || err.message || 'Could not fetch contracts.',
        }));
      } finally {
        if (mounted) setLoadingContracts(false);
      }
    })();

    return () => {
      mounted = false;
    };
  }, [dispatch]);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const response = await generationService.getTemplates();
        if (!mounted) return;
        setTemplates(response.templates || []);
      } catch (err) {
        if (!mounted) return;
        dispatch(showToast({
          type: 'error',
          title: 'Failed to Load Templates',
          message: err.response?.data?.detail || err.message || 'Could not fetch template list.',
        }));
      } finally {
        if (mounted) setLoadingTemplates(false);
      }
    })();

    return () => {
      mounted = false;
    };
  }, [dispatch]);

  const analyzableContracts = useMemo(
    () => contracts.filter(c => c.analysis_status === 'completed'),
    [contracts]
  );

  const contractOptions = analyzableContracts.map(c => ({
    value: c.id,
    label: c.title || c.filename,
  }));

  const formatOptions = [
    { value: 'pdf', label: 'PDF' },
    { value: 'docx', label: 'DOCX' },
  ];
  const templateOptions = templates.map(t => ({ value: t.id, label: t.name }));

  const selectedContract = analyzableContracts.find(c => c.id === selectedContractId);
  const selectedTemplate = templates.find(t => t.id === selectedTemplateId);

  const handleTemplateInput = (field) => (eventOrValue) => {
    const value = typeof eventOrValue === 'string'
      ? eventOrValue
      : eventOrValue?.target?.value ?? '';
    setTemplateForm(prev => ({ ...prev, [field]: value }));
  };

  const handleTemplatePreview = async () => {
    if (!selectedTemplateId) return;
    setTemplatePreviewing(true);
    try {
      const res = await generationService.previewFromTemplate(selectedTemplateId, templateForm);
      setTemplatePreviewText(res.preview_text || '');
      dispatch(showToast({
        type: 'success',
        title: 'Template Preview Ready',
        message: `${res.template_name || 'Contract template'} draft is ready.`,
      }));
    } catch (err) {
      dispatch(showToast({
        type: 'error',
        title: 'Template Preview Failed',
        message: err.response?.data?.detail || err.message || 'Could not build template preview.',
      }));
    } finally {
      setTemplatePreviewing(false);
    }
  };

  const handlePreview = async () => {
    if (!selectedContractId) return;
    setPreviewing(true);
    try {
      const res = await generationService.previewFromContract(selectedContractId);
      setPreviewText(res.preview_text || '');
      dispatch(showToast({
        type: 'success',
        title: 'Preview Ready',
        message: 'Generated contract preview loaded.',
      }));
    } catch (err) {
      dispatch(showToast({
        type: 'error',
        title: 'Preview Failed',
        message: err.response?.data?.detail || err.message || 'Could not generate preview.',
      }));
    } finally {
      setPreviewing(false);
    }
  };

  const handleGenerate = async () => {
    if (!selectedContractId) return;
    setGenerating(true);
    try {
      const res = await generationService.generateFromContract(
        selectedContractId,
        format,
        includeSummary
      );
      setGeneratedDoc(res);
      dispatch(showToast({
        type: 'success',
        title: 'Contract Generated',
        message: `Version ${res.version || ''} generated successfully.`,
      }));
    } catch (err) {
      dispatch(showToast({
        type: 'error',
        title: 'Generation Failed',
        message: err.response?.data?.detail || err.message || 'Could not generate contract.',
      }));
    } finally {
      setGenerating(false);
    }
  };

  const openDownload = () => {
    if (generatedDoc?.download_url) {
      window.open(generatedDoc.download_url, '_blank', 'noopener,noreferrer');
    }
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
          Generate a new AI-reviewed contract version from your analyzed contracts.
        </p>
      </div>

      <Card className="p-8">
        <div className="space-y-6">
          <h2 className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>
            Create From Template
          </h2>
          <p style={{ color: 'var(--color-text-tertiary)' }}>
            Start from a legal template and fill key details to generate a balanced draft.
          </p>

          <Select
            label="Contract Template"
            options={templateOptions}
            value={selectedTemplateId}
            onChange={(value) => {
              setSelectedTemplateId(value);
              setTemplatePreviewText('');
            }}
            placeholder={loadingTemplates ? 'Loading templates...' : 'Choose a template'}
            disabled={loadingTemplates}
          />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Input
              label="Party 1 Name"
              value={templateForm.party_1_name}
              onChange={handleTemplateInput('party_1_name')}
              placeholder="e.g., ABC Pvt Ltd"
            />
            <Input
              label="Party 2 Name"
              value={templateForm.party_2_name}
              onChange={handleTemplateInput('party_2_name')}
              placeholder="e.g., John Smith"
            />
            <Input
              label="Effective Date"
              type="date"
              value={templateForm.effective_date}
              onChange={handleTemplateInput('effective_date')}
            />
            <Input
              label="Term (Months)"
              value={templateForm.term_months}
              onChange={handleTemplateInput('term_months')}
              placeholder="12"
            />
            <Input
              label="Governing Law"
              value={templateForm.governing_law}
              onChange={handleTemplateInput('governing_law')}
              placeholder="e.g., California, USA"
            />
            <Input
              label="Payment Terms"
              value={templateForm.payment_terms}
              onChange={handleTemplateInput('payment_terms')}
              placeholder="e.g., Net 30 invoice"
            />
          </div>

          {selectedTemplate && (
            <div className="grid grid-cols-1 gap-4">
              {selectedTemplate.id === 'mutual_nda' && (
                <Textarea
                  label="Purpose"
                  rows={3}
                  value={templateForm.purpose}
                  onChange={handleTemplateInput('purpose')}
                  placeholder="Why both parties share confidential information..."
                />
              )}

              {selectedTemplate.id === 'service_agreement' && (
                <Textarea
                  label="Scope of Services"
                  rows={3}
                  value={templateForm.scope_of_services}
                  onChange={handleTemplateInput('scope_of_services')}
                  placeholder="Describe service scope..."
                />
              )}

              {selectedTemplate.id === 'employment_offer' && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Input
                    label="Position Title"
                    value={templateForm.position_title}
                    onChange={handleTemplateInput('position_title')}
                    placeholder="Software Engineer"
                  />
                  <Input
                    label="Base Salary"
                    value={templateForm.base_salary}
                    onChange={handleTemplateInput('base_salary')}
                    placeholder="$80,000/year"
                  />
                  <Input
                    label="Termination Notice (Days)"
                    value={templateForm.termination_notice_days}
                    onChange={handleTemplateInput('termination_notice_days')}
                    placeholder="30"
                  />
                </div>
              )}

              {selectedTemplate.id === 'consulting_agreement' && (
                <Textarea
                  label="Deliverables"
                  rows={3}
                  value={templateForm.deliverables}
                  onChange={handleTemplateInput('deliverables')}
                  placeholder="List consultant deliverables..."
                />
              )}
            </div>
          )}

          <Textarea
            label="Additional Terms"
            rows={3}
            value={templateForm.additional_terms}
            onChange={handleTemplateInput('additional_terms')}
            placeholder="Optional custom clauses or constraints..."
          />

          <Button
            onClick={handleTemplatePreview}
            className="w-full"
            variant="outline"
            loading={templatePreviewing}
            disabled={!selectedTemplateId}
          >
            Preview Template Draft
          </Button>
        </div>
      </Card>

      {templatePreviewText && (
        <Card className="p-8">
          <div className="space-y-4">
            <h2 className="text-xl font-bold" style={{ color: 'var(--color-text-primary)' }}>
              Template Draft Preview
            </h2>
            <div className="p-6 rounded-xl border max-h-96 overflow-y-auto" style={{ backgroundColor: 'var(--color-bg-tertiary)', borderColor: 'var(--color-neutral-200)' }}>
              <p className="text-sm whitespace-pre-line" style={{ color: 'var(--color-text-secondary)' }}>
                {templatePreviewText}
              </p>
            </div>
          </div>
        </Card>
      )}

      <Card className="p-8">
        <div className="space-y-6">
          <h2 className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>
            Generate From Uploaded Contract
          </h2>

          <Select
            label="Select Analyzed Contract"
            options={contractOptions}
            value={selectedContractId}
            onChange={setSelectedContractId}
            placeholder={loadingContracts ? 'Loading contracts...' : 'Choose a contract'}
            disabled={loadingContracts}
            helperText="Only contracts with completed analysis are shown."
          />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Select
              label="Output Format"
              options={formatOptions}
              value={format}
              onChange={setFormat}
            />
            <label className="flex items-center gap-3 mt-8 md:mt-10">
              <input
                type="checkbox"
                checked={includeSummary}
                onChange={(e) => setIncludeSummary(e.target.checked)}
                className="w-4 h-4"
              />
              <span style={{ color: 'var(--color-text-secondary)' }}>Include analysis summary page</span>
            </label>
          </div>

          {selectedContract && (
            <div className="p-4 rounded-xl border" style={{ borderColor: 'var(--color-neutral-200)', backgroundColor: 'var(--color-bg-tertiary)' }}>
              <div className="flex items-center gap-3">
                <FileText className="w-5 h-5" style={{ color: 'var(--color-primary-600)' }} />
                <div>
                  <p className="font-semibold" style={{ color: 'var(--color-text-primary)' }}>
                    {selectedContract.title || selectedContract.filename}
                  </p>
                  <p className="text-sm" style={{ color: 'var(--color-text-tertiary)' }}>
                    High risk: {selectedContract.high_risk_count || 0} | Risk score: {selectedContract.overall_risk_score || 0}
                  </p>
                </div>
              </div>
            </div>
          )}

          {analyzableContracts.length === 0 && !loadingContracts && (
            <div className="p-4 rounded-xl border" style={{ borderColor: 'var(--color-warning)', backgroundColor: 'var(--color-warning-light)' }}>
              <p style={{ color: 'var(--color-warning)' }}>
                No analyzed contracts found. Upload and analyze a contract first.
              </p>
            </div>
          )}

          <div className="flex flex-col sm:flex-row gap-3">
            <Button
              onClick={handlePreview}
              className="flex-1 gap-2"
              size="lg"
              variant="outline"
              loading={previewing}
              disabled={!selectedContractId}
            >
              Preview Generated Contract
            </Button>

            <Button
              onClick={handleGenerate}
              className="flex-1 gap-2 glow"
              size="lg"
              loading={generating}
              disabled={!selectedContractId}
            >
              <FileCheck className="w-5 h-5" style={{ color: 'white' }} />
              Generate Contract
            </Button>
          </div>
        </div>
      </Card>

      {previewText && (
        <Card className="p-8">
          <div className="space-y-4">
            <h2 className="text-xl font-bold" style={{ color: 'var(--color-text-primary)' }}>
              Generated Preview
            </h2>
            <div className="p-6 rounded-xl border max-h-96 overflow-y-auto" style={{ backgroundColor: 'var(--color-bg-tertiary)', borderColor: 'var(--color-neutral-200)' }}>
              <p className="text-sm whitespace-pre-line" style={{ color: 'var(--color-text-secondary)' }}>
                {previewText}
              </p>
            </div>
          </div>
        </Card>
      )}

      {generatedDoc && (
        <Card className="p-8">
          <div className="space-y-6">
            <div className="flex items-center gap-4 p-4 rounded-2xl" style={{ background: 'var(--color-success-light)' }}>
              <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ background: 'var(--color-success)' }}>
                <FileCheck className="w-6 h-6" style={{ color: 'white' }} />
              </div>
              <div>
                <h2 className="text-xl font-bold" style={{ color: 'var(--color-success)' }}>Contract Generated</h2>
                <p className="text-sm" style={{ color: 'var(--color-success)' }}>
                  {generatedDoc.filename} ({generatedDoc.file_size_kb} KB)
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-4 rounded-lg border" style={{ borderColor: 'var(--color-neutral-200)' }}>
                <p className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>Version</p>
                <p className="font-semibold" style={{ color: 'var(--color-text-primary)' }}>{generatedDoc.version}</p>
              </div>
              <div className="p-4 rounded-lg border" style={{ borderColor: 'var(--color-neutral-200)' }}>
                <p className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>Applied Suggestions</p>
                <p className="font-semibold" style={{ color: 'var(--color-text-primary)' }}>{generatedDoc.applied_suggestions_count || 0}</p>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-3">
              <Button className="flex-1 gap-2" onClick={openDownload}>
                <Download className="w-4 h-4" style={{ color: 'white' }} />
                Download Generated Contract
              </Button>
              <Button
                variant="ghost"
                onClick={() => {
                  setGeneratedDoc(null);
                  setPreviewText('');
                }}
              >
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
