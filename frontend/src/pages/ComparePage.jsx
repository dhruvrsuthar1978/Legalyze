import { useState } from 'react';
import { Upload } from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';

function ComparePage() {
  const [file1, setFile1] = useState(null);
  const [file2, setFile2] = useState(null);
  const [comparing, setComparing] = useState(false);
  const [compared, setCompared] = useState(false);

  const handleCompare = () => {
    setComparing(true);
    setTimeout(() => {
      setComparing(false);
      setCompared(true);
    }, 2000);
  };

  const differences = [
    { clause: 'Termination Notice Period', contract1: '30 days', contract2: '60 days', type: 'different' },
    { clause: 'Non-Compete Duration', contract1: '2 years', contract2: '1 year', type: 'different' },
    { clause: 'Severance Pay', contract1: 'Not mentioned', contract2: '3 months salary', type: 'missing' },
    { clause: 'Intellectual Property', contract1: 'All work products', contract2: 'Work-related only', type: 'different' },
  ];

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold" style={{ color: 'var(--color-text-primary)' }}>Compare Contracts 🔄</h1>
        <p className="mt-1" style={{ color: 'var(--color-text-tertiary)' }}>Compare two contracts side-by-side to identify differences</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <h3 className="text-lg font-semibold mb-4" style={{ color: 'var(--color-text-primary)' }}>Contract 1</h3>
          <div className="border-2 border-dashed rounded-lg p-8 text-center" style={{ borderColor: 'var(--color-neutral-300)' }}>
            {!file1 ? (
              <>
                <Upload className="w-12 h-12 mx-auto mb-3" style={{ color: 'var(--color-neutral-400)' }} />
                <p className="text-sm mb-3" style={{ color: 'var(--color-text-tertiary)' }}>Upload first contract</p>
                <input
                  type="file"
                  id="file1"
                  className="hidden"
                  onChange={(e) => setFile1(e.target.files[0])}
                  accept=".pdf,.docx"
                />
                <label htmlFor="file1">
                  <Button as="span" size="sm" className="cursor-pointer">
                    Select File
                  </Button>
                </label>
              </>
            ) : (
              <div className="text-left">
                <p className="font-medium" style={{ color: 'var(--color-text-primary)' }}>{file1.name}</p>
                <p className="text-sm mt-1" style={{ color: 'var(--color-text-tertiary)' }}>
                  {(file1.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            )}
          </div>
        </Card>

        <Card>
          <h3 className="text-lg font-semibold mb-4" style={{ color: 'var(--color-text-primary)' }}>Contract 2</h3>
          <div className="border-2 border-dashed rounded-lg p-8 text-center" style={{ borderColor: 'var(--color-neutral-300)' }}>
            {!file2 ? (
              <>
                <Upload className="w-12 h-12 mx-auto mb-3" style={{ color: 'var(--color-neutral-400)' }} />
                <p className="text-sm mb-3" style={{ color: 'var(--color-text-tertiary)' }}>Upload second contract</p>
                <input
                  type="file"
                  id="file2"
                  className="hidden"
                  onChange={(e) => setFile2(e.target.files[0])}
                  accept=".pdf,.docx"
                />
                <label htmlFor="file2">
                  <Button as="span" size="sm" className="cursor-pointer">
                    Select File
                  </Button>
                </label>
              </>
            ) : (
              <div className="text-left">
                <p className="font-medium" style={{ color: 'var(--color-text-primary)' }}>{file2.name}</p>
                <p className="text-sm mt-1" style={{ color: 'var(--color-text-tertiary)' }}>
                  {(file2.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            )}
          </div>
        </Card>
      </div>

      {file1 && file2 && !compared && (
        <div className="text-center">
          <Button onClick={handleCompare} size="lg" loading={comparing}>
            Compare Contracts
          </Button>
        </div>
      )}

      {compared && (
        <Card>
          <h2 className="text-xl font-semibold mb-6" style={{ color: 'var(--color-text-primary)' }}>Comparison Results</h2>
          <div className="space-y-4">
            {differences.map((diff, index) => (
              <div key={index} className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 rounded-lg" style={{ backgroundColor: 'var(--color-bg-tertiary)' }}>
                <div>
                  <p className="text-sm font-medium mb-1" style={{ color: 'var(--color-text-secondary)' }}>{diff.clause}</p>
                  <Badge variant={diff.type === 'different' ? 'warning' : 'error'}>
                    {diff.type === 'different' ? 'Different' : 'Missing in Contract 1'}
                  </Badge>
                </div>
                <div>
                  <p className="text-xs mb-1" style={{ color: 'var(--color-text-tertiary)' }}>Contract 1</p>
                  <p className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>{diff.contract1}</p>
                </div>
                <div>
                  <p className="text-xs mb-1" style={{ color: 'var(--color-text-tertiary)' }}>Contract 2</p>
                  <p className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>{diff.contract2}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}

export default ComparePage;