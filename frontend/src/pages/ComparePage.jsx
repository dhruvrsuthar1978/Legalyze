import { useState } from 'react';
import { Upload } from 'lucide-react';
import { useDispatch } from 'react-redux';
import { contractService } from '../services/contractService';
import { showToast } from '../store/uiSlice';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';

function ComparePage() {
  const dispatch = useDispatch();
  const [file1, setFile1] = useState(null);
  const [file2, setFile2] = useState(null);
  const [comparing, setComparing] = useState(false);
  const [compared, setCompared] = useState(false);
  const [differences, setDifferences] = useState([]);

  const handleCompare = () => {
    setComparing(true);

    // Call backend compare endpoint
    contractService.compareContracts(file1, file2)
      .then((res) => {
        setComparing(false);
        setCompared(true);

        // Parse unified diff-like lines into structured items
        if (res.differences && Array.isArray(res.differences)) {
          const diffLines = res.differences.map(d => d.text || d);
          const parsed = parseUnifiedDiff(diffLines);
          setDifferences(parsed);
        } else {
          setDifferences([]);
        }
      })
      .catch((err) => {
        setComparing(false);
        dispatch(showToast({
          type: 'error',
          title: 'Compare Failed',
          message: err.response?.data?.detail || err.message || 'Compare failed',
        }));
      });
  };


  // Parse unified diff lines into structured difference objects
  function parseUnifiedDiff(lines) {
    const hunks = [];
    let current = { removed: [], added: [], context: [] };

    for (const raw of lines) {
      const line = raw.replace(/\r$/, '');

      if (line.startsWith('@@')) {
        // start new hunk
        if (current.removed.length || current.added.length || current.context.length) {
          hunks.push(current);
        }
        current = { removed: [], added: [], context: [] };
        continue;
      }

      if (line.startsWith('-')) {
        current.removed.push(line.slice(1).trim());
      } else if (line.startsWith('+')) {
        current.added.push(line.slice(1).trim());
      } else if (line.startsWith(' ')) {
        current.context.push(line.slice(1).trim());
      } else {
        // sometimes diff lines may be plain text
        current.context.push(line.trim());
      }
    }

    if (current.removed.length || current.added.length || current.context.length) {
      hunks.push(current);
    }

    // Convert hunks to UI-friendly items
    const items = hunks.map(h => {
      const removedText = h.removed.join(' ') || null;
      const addedText = h.added.join(' ') || null;
      const contextText = h.context.join(' ') || '';

      let type = 'different';
      if (removedText && !addedText) type = 'missing';
      if (!removedText && addedText) type = 'added';

      const clauseLabel = contextText || (removedText || addedText) || 'Difference';

      return {
        clause: clauseLabel,
        contract1: removedText || '',
        contract2: addedText || '',
        type
      };
    });

    return items;
  }

  

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
                  aria-label="Upload first contract for comparison"
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
                  aria-label="Upload second contract for comparison"
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
              <div key={index} className="p-4 rounded-lg" style={{ backgroundColor: 'var(--color-bg-tertiary)' }}>
                <div className="flex items-start justify-between gap-4 mb-3">
                  <div className="flex-1">
                    <p className="text-sm font-medium mb-1" style={{ color: 'var(--color-text-secondary)' }}>{diff.clause}</p>
                    <Badge variant={diff.type === 'different' ? 'warning' : diff.type === 'missing' ? 'danger' : 'success'}>
                      {diff.type === 'different' ? 'Different' : diff.type === 'missing' ? 'Missing' : 'Added'}
                    </Badge>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs mb-1" style={{ color: 'var(--color-text-tertiary)' }}>Contract 1</p>
                    <div className="p-3 rounded-md" style={{ backgroundColor: 'white', border: '1px solid var(--color-neutral-200)' }}>
                      {renderHighlighted(diff.contract1 || '', diff.contract2 || '', 'left')}
                    </div>
                  </div>
                  <div>
                    <p className="text-xs mb-1" style={{ color: 'var(--color-text-tertiary)' }}>Contract 2</p>
                    <div className="p-3 rounded-md" style={{ backgroundColor: 'white', border: '1px solid var(--color-neutral-200)' }}>
                      {renderHighlighted(diff.contract1 || '', diff.contract2 || '', 'right')}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}

// Simple word-level highlighter: marks differing words between left and right
function renderHighlighted(leftText, rightText, side = 'left') {
  const leftWords = leftText ? leftText.split(/(\s+)/) : [];
  const rightWords = rightText ? rightText.split(/(\s+)/) : [];
  const maxLen = Math.max(leftWords.length, rightWords.length);
  const nodes = [];

  for (let i = 0; i < maxLen; i++) {
    const lw = leftWords[i] ?? '';
    const rw = rightWords[i] ?? '';

    const isDifferent = lw.trim() !== rw.trim();

    const word = side === 'left' ? lw : rw;

    if (isDifferent && word.trim()) {
      nodes.push(
        <span key={i} style={{ backgroundColor: 'rgba(250, 223, 132, 0.6)', padding: '2px 4px', borderRadius: 4, marginRight: 2 }}>{word}</span>
      );
    } else {
      nodes.push(
        <span key={i} style={{ marginRight: 2 }}>{word}</span>
      );
    }
  }

  return <div className="text-sm" style={{ color: 'var(--color-text-primary)' }}>{nodes}</div>;
}

export default ComparePage;
