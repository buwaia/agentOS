import { useState, useEffect } from "react";
import { api } from "./services/api";
import { SubmitForm } from "./components/SubmitForm";
import { JobList } from "./components/JobList";
import { JobDetail } from "./components/JobDetail";

export default function App() {
  const [jobs, setJobs] = useState([]);
  const [selectedId, setSelectedId] = useState(null);

  useEffect(() => {
    api
      .listJobs()
      .then(setJobs)
      .catch(() => {});
  }, []);

  const handleJobCreated = (job) => {
    setJobs((prev) => [job, ...prev]);
    setSelectedId(job.job_id);
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white border-b border-gray-200 px-6 py-4 shadow-sm">
        <h1 className="text-xl font-bold text-gray-900">
          Math Solver — Delivery Engine
        </h1>
        <p className="text-xs text-gray-500 mt-0.5">
          UNDERSTAND → ORIENT → SOLVE → VERIFY
        </p>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-6 space-y-6">
        {/* How-it-works banner */}
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 text-sm text-blue-900">
          <div className="font-semibold mb-2">这个系统是什么？</div>
          <p className="mb-2">
            数学解题引擎——你输入一道数学题，系统通过四个阶段帮你产出
            <strong>通俗易懂的解题过程</strong>：
          </p>
          <ol className="list-decimal list-inside space-y-1 text-blue-800 mb-3">
            <li>
              <strong>UNDERSTAND</strong>：AI
              自动分析题目类型、已知条件、求解目标（G1 置信度门禁）
            </li>
            <li>
              <strong>ORIENT</strong>：选择解题路径，
              <span className="bg-yellow-100 px-1 rounded">
                需人工审批（G2）
              </span>
              确认方向正确
            </li>
            <li>
              <strong>SOLVE</strong>：逐步推导，每步必须有原因 + 直觉解释（G3
              质量门禁）
            </li>
            <li>
              <strong>VERIFY</strong>：验证所有步骤，确认解析有直觉描述（G4
              完整性门禁）
            </li>
          </ol>
          <div className="font-semibold mb-1">怎么操作？</div>
          <ol className="list-decimal list-inside space-y-1 text-blue-800">
            <li>在下方输入框提交题目 → 系统自动完成 UNDERSTAND</li>
            <li>
              在 Job 详情里点击 <strong>Approve / Reject</strong> 完成 G2 审批
            </li>
            <li>填写 SOLVE 表单（推导步骤 + 直觉解释）</li>
            <li>
              填写 VERIFY 表单 → 状态变为{" "}
              <strong className="text-green-700">done</strong>
            </li>
          </ol>
          <div className="mt-2 text-xs text-blue-600">
            产出效果：每个通过 G4 的 Job 都有「有原因的推导 +
            直觉解释」，可直接用于教学或复盘。 Gate 事件自动写入
            DynamoDB，/drishti 定期蒸馏成治理规则。
          </div>
        </div>

        {/* Top: submit */}
        <SubmitForm onJobCreated={handleJobCreated} />

        {/* Middle + Bottom: two-column */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Job list */}
          <div className="md:col-span-1 bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
            <h2 className="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wide">
              Jobs ({jobs.length})
            </h2>
            <JobList
              jobs={jobs}
              selectedId={selectedId}
              onSelect={setSelectedId}
            />
          </div>

          {/* Job detail */}
          <div className="md:col-span-2 bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
            <h2 className="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wide">
              Detail
            </h2>
            <JobDetail jobId={selectedId} />
          </div>
        </div>
      </main>
    </div>
  );
}
