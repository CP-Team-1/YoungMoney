import './LessonProgress.css'

export default function LessonProgress({ current, total }) {
  return (
    <div className="lesson-progress">
      {Array.from({ length: total }, (_, i) => (
        <div
          key={i}
          className={`lesson-progress__dot${i < current ? ' lesson-progress__dot--done' : i === current ? ' lesson-progress__dot--active' : ''}`}
        />
      ))}
    </div>
  )
}
