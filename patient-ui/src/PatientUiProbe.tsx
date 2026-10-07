export type PatientUiProbeProps = {
  label?: string
}

export function PatientUiProbe({
  label = "React island build is isolated and ready.",
}: PatientUiProbeProps) {
  return (
    <section
      className="kgg-react-island kgg-react-probe"
      data-kgg-react-probe="p4-skeleton"
    >
      <p className="kgg-react-probe__eyebrow">KGG patient UI</p>
      <h1 className="kgg-react-probe__title">React island probe</h1>
      <p className="kgg-react-probe__copy">{label}</p>
    </section>
  )
}
